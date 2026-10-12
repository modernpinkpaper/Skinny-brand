"""Human-Dynamic voiceover pipeline (VOICEOVER_FORMULA v1) using Chatterbox Nano."""
import hashlib, os, re, json, subprocess, warnings, difflib, time, sys
import numpy as np, soundfile as sf, librosa, torch, pyloudnorm as pyln
from num2words import num2words
warnings.filterwarnings("ignore")
torch.set_num_threads(4)

W = "vo"; INP = f"{W}/inputs"; CL = f"{W}/clips"; OUT = sys.argv[1]
os.makedirs(CL, exist_ok=True); os.makedirs(OUT, exist_ok=True)
SR = 24000
SEEDS = [1947, 1948, 1949, 2051, 2052, 3011, 3012, 4099]
TONE = "warm"; INTENSITY = 5
BASE = 0.82  # Nano reads ~3.7 words/s; speaker is ~2.0-3.3 words/s, so calibrate the base rate first

# ---------------------------------------------------------------- script ----
# (section cue, reference tone, [(text, inline cue, speed factor, pause after s)])
SECTIONS = [
 ("gentle opening", "warm", [
   ("I went back through my logs to see what my last recorded day really looked like.", "gentle; deliberate", (0.96, 1.02, 0.95), 0.35),
   ("It was Sunday, October eleventh.", "easy", (0.97, 1.00, 0.94), 0.30),
   ("And honestly? It was quiet.", "soft; small smile; slower", (0.96, 1.00, 0.93), 0.55)]),
 ("build; slightly faster", "warm", [
   ("Just before nine that morning, my system woke up on its own and did the one job I gave it.", "conversational", (0.98, 1.08, 0.97), 0.30),
   ("It sent three finished videos to my TikTok drafts.", "brisk", (1.00, 1.10, 0.97), 0.30),
   ("The first was, being needed is not being loved.", "light emphasis on the title", (0.98, 1.06, 0.96), 0.30),
   ("The second, help is the sunny side of control.", "quicker", (1.00, 1.10, 0.97), 0.30),
   ("And the third, the mortifying ordeal of being known.", "ease down; land it", (0.98, 1.05, 0.93), 0.50)]),
 ("matter-of-fact; steady", "warm", [
   ("That's it. No big launch, no drama, just a small run that got the job done.", "short and flat, then relaxed; slightly faster", (0.97, 1.07, 0.96), 0.25),
   ("Same quiet routine as Friday and Saturday.", "easy", (0.98, 1.05, 0.96), 0.25),
   ("Forty-four videos sent so far.", "settle; slower", (0.97, 1.00, 0.93), 0.65)]),
 ("key point; slower; pause before", "warm", [
   ("A quiet day in the log is not an empty day.", "slower; reassuring", (0.96, 1.00, 0.93), 0.45),
   ("Showing up quietly is still showing up.", "warm; a touch quicker", (0.97, 1.02, 0.94), 0.50),
   ("And tomorrow morning, it will show up again.", "slowest; soft landing", (0.95, 0.99, 0.91), 0.0)]),
]
flat = []  # one record per sentence
for si, (cue, tone, sents) in enumerate(SECTIONS):
    for ti, (t, c, f, p) in enumerate(sents):
        flat.append(dict(sec=si, tone=tone, text=t, cue=c, factor=f, pause=p, first=(ti == 0)))

marked = [f"# Marked production script\n\nTone: {TONE} and conversational · Intensity: {INTENSITY}/10 · Formula: Approved Human-Dynamic Voice Formula v1\n"]
clean = []
for si, (cue, tone, sents) in enumerate(SECTIONS):
    marked.append(f"\n[{cue}]")
    line = []
    for (t, c, f, p) in sents:
        pz = f" [pause {int(p*1000)} ms]" if p else ""
        line.append(f"[{c}; pace {f[0]:.2f}x > {f[1]:.2f}x > {f[2]:.2f}x] {t}{pz}")
    marked.append("\n".join(line))
    clean.append(" ".join(t for t, *_ in sents))
open(f"{OUT}/marked-script.md", "w").write("\n".join(marked) + "\n")
open(f"{OUT}/clean-script.txt", "w").write("\n\n".join(clean) + "\n")
CUE_WORDS = set()
for cue, _, sents in SECTIONS:
    for w in re.findall(r"[a-z]+", " ".join([cue] + [c for _, c, _, _ in sents]).lower()): CUE_WORDS.add(w)
SCRIPT_WORDS = set(re.findall(r"[a-z]+", " ".join(clean).lower()))
CUE_WORDS = {w for w in CUE_WORDS - SCRIPT_WORDS if len(w) > 3}

# ------------------------------------------------------------- helpers ------
def norm_words(s):
    s = s.lower().replace("-", " ").replace("tik tok", "tiktok")
    s = re.sub(r"(\d+)(st|nd|rd|th)\b", lambda m: num2words(int(m.group(1)), to="ordinal"), s)
    s = re.sub(r"\d+", lambda m: num2words(int(m.group(0))), s)
    s = s.replace("-", " ")
    return re.findall(r"[a-z']+", s)

def wer(ref, hyp):
    r, h = norm_words(ref), norm_words(hyp)
    if "".join(r) == "".join(h): return 0.0
    sm = difflib.SequenceMatcher(None, r, h)
    return 1 - sm.ratio()

def emb_of(m, w16): return np.mean(m.ve.embeds_from_wavs([w16], sample_rate=16000), axis=0)
def cos(a, b): return float(np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b))

def trim(w, margin=0.03):
    _, (a, b) = librosa.effects.trim(w, top_db=38)
    a = max(0, a - int(margin * SR)); b = min(len(w), b + int(margin * SR))
    w = w[a:b].copy(); n = int(0.012 * SR)
    w[:n] *= np.linspace(0, 1, n); w[-n:] *= np.linspace(1, 0, n)
    return w

def stretch(w, f, tag):
    if abs(f - 1) < 1e-3: return w
    a, b = f"{W}/_s_in_{tag}.wav", f"{W}/_s_out_{tag}.wav"
    sf.write(a, w, SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af", f"rubberband=tempo={f:.4f}:pitch=1:transients=smooth", b], check=True)
    o = sf.read(b)[0].astype(np.float32); os.remove(a); os.remove(b); return o

def zone_stretch(i, w, wts):
    """Split one take at quiet points between words and stretch open/body/end separately (pitch preserved)."""
    r = flat[i]; fo, fb, fe = r["factor"]; n = len(norm_words(r["text"]))
    ko = 2 if n <= 6 else 3; ke = 2 if n <= 6 else 3
    if n <= 4: ko, ke = 2, 0
    dur = len(w) / SR
    tw = [(x.start, x.end) for x in wts]
    def cut(k):  # time between word k-1 and word k
        if len(tw) == n and 0 < k < n: t = (tw[k - 1][1] + tw[k][0]) / 2
        else: t = dur * k / n
        a = int(max(0.05, t - 0.06) * SR); b = int(min(dur - 0.05, t + 0.06) * SR)
        env = np.convolve(np.abs(w[a:b]), np.ones(int(0.008 * SR)) / int(0.008 * SR), mode="same")
        return (a + int(np.argmin(env))) / SR
    cuts = [0.0]
    if ko: cuts.append(cut(ko))
    if ke and n - ke > ko: cuts.append(cut(n - ke))
    cuts.append(dur)
    roles = []; nw = []
    bounds = [0] + ([ko] if ko else []) + ([n - ke] if (ke and n - ke > ko) else []) + [n]
    names = ["open", "body", "end"] if len(cuts) == 4 else (["open", "end"] if len(cuts) == 3 else ["open"])
    facts = {"open": fo, "body": fb, "end": fe}
    if len(cuts) == 3 and not (ke and n - ke > ko): names = ["open", "body"]
    xo = int(0.010 * SR); pieces = []; info = []
    for j, nm in enumerate(names):
        a = int(cuts[j] * SR); b = int(cuts[j + 1] * SR)
        seg = w[max(0, a - (xo if j else 0)): min(len(w), b + (xo if j < len(names) - 1 else 0))].copy()
        st = stretch(seg, BASE * facts[nm], f"{i}_{j}")
        pieces.append(st); info.append(dict(zone=nm, words=bounds[j + 1] - bounds[j], factor=facts[nm], seconds=len(st) / SR))
    out = join(pieces, [0.0] * (len(pieces) - 1)) if len(pieces) > 1 else pieces[0]
    return out, info

def join(clips, pauses, xf=0.020):
    n = int(xf * SR); out = clips[0]
    for c, p in zip(clips[1:], pauses):
        out = np.concatenate([out, np.zeros(int(p * SR), dtype=np.float32)])
        a = out[-n:] ; b = c[:n]
        t = np.linspace(0, np.pi / 2, n)
        mix = a * np.cos(t) + b * np.sin(t)
        out = np.concatenate([out[:-n], mix, c[n:]])
    return out

# --------------------------------------------------------------- models -----
from chatterbox.tts_turbo import ChatterboxTurboTTS
from faster_whisper import WhisperModel
m = ChatterboxTurboTTS.from_pretrained(device="cpu", nano=True)
asr = WhisperModel("small.en", device="cpu", compute_type="int8")
asr2 = WhisperModel("medium.en", device="cpu", compute_type="int8")
def transcribe(path_or_arr, words=False, model=None):
    model = model or asr
    segs, _ = model.transcribe(path_or_arr, beam_size=5, language="en", word_timestamps=words, condition_on_previous_text=False, temperature=0.0)
    segs = list(segs); txt = " ".join(s.text.strip() for s in segs)
    return (txt, [w for s in segs for w in s.words]) if words else txt

full16 = librosa.load(f"{INP}/original-16k.wav", sr=16000)[0]
REAL = np.mean([emb_of(m, full16[i:i + 160000]) for i in range(0, len(full16) - 160000, 16000 * 40)], axis=0)

# ------------------------------------------------------ per-phrase gen -----
qc = dict(phrases=[], rounds=[])
def gen_phrase(i, banned_seeds=()):
    r = flat[i]; ref = f"{INP}/voice-tone-{r['tone']}.wav"; best = None; tries = []
    for seed in SEEDS:
        if seed in banned_seeds: continue
        cache = f"{CL}/{hashlib.md5(r['text'].encode()).hexdigest()[:8]}_{seed}.wav"
        if os.path.exists(cache): w = sf.read(cache)[0].astype(np.float32)
        else:
            torch.manual_seed(seed); np.random.seed(seed)
            w = m.generate(r["text"], audio_prompt_path=ref, temperature=0.7, top_p=0.95, repetition_penalty=1.2).squeeze().cpu().numpy().astype(np.float32)
            sf.write(cache, w, SR)
        w = trim(w); dur = len(w) / SR; n = len(norm_words(r["text"]))
        hyp, wts = transcribe(librosa.resample(w, orig_sr=SR, target_sr=16000), words=True)
        e = wer(r["text"], hyp); sim = cos(REAL, emb_of(m, librosa.resample(w, orig_sr=SR, target_sr=16000)))
        wps = n / dur; peak = float(np.abs(w).max())
        ok = e == 0 and 1.5 <= wps <= 4.6 and (sim >= 0.78 or dur < 1.5) and peak < 0.98
        tries.append(dict(seed=seed, wer=round(e, 3), sim=round(sim, 3), wps=round(wps, 2), ok=ok, heard=hyp))
        print(f"  p{i:02d} seed {seed}: wer={e:.2f} sim={sim:.3f} wps={wps:.2f} {'OK' if ok else 'reject'}  | {hyp}", flush=True)
        key = (e, -sim)
        if best is None or key < best[0]: best = (key, (w, wts), seed)
        if ok: return (w, wts), seed, tries
    print(f"  p{i:02d}: no seed fully passed, using best", flush=True)
    return best[1], best[2], tries

phr = {}
for i in range(len(flat)):
    print(f"[{i+1}/{len(flat)}] {flat[i]['text']}", flush=True)
    w, seed, tries = gen_phrase(i)
    phr[i] = dict(w=w, seed=seed, tries=tries)

# ------------------------------------------------------------ assemble ------
def assemble():
    clips = []; durs = []; global zinfo; zinfo = {}
    for i, r in enumerate(flat):
        w, wts = phr[i]["w"]
        s, zinfo[i] = zone_stretch(i, w, wts); clips.append(s); durs.append(len(s) / SR)
    pauses = [r["pause"] for r in flat[:-1]]
    return join(clips, pauses), clips, durs

ref_w = librosa.load(f"{INP}/voice-tone-{TONE}.wav", sr=SR)[0]
meter = pyln.Meter(SR); REF_LUFS = meter.integrated_loudness(ref_w)

def finish(audio):
    lufs = meter.integrated_loudness(audio)
    audio = audio * (10 ** ((REF_LUFS - lufs) / 20))
    tmp, tmp2 = f"{W}/_l_in.wav", f"{W}/_l_out.wav"
    sf.write(tmp, audio, SR, subtype="FLOAT")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", "alimiter=limit=0.7079:attack=5:release=60:level=disabled", tmp2], check=True)
    o = sf.read(tmp2)[0].astype(np.float32); os.remove(tmp); os.remove(tmp2)
    return o

clean_text = " ".join(t for t, *_ in [s for _, _, ss in SECTIONS for s in ss])
all_words = []
for rnd in range(4):
    audio, clips, durs = assemble(); final = finish(audio)
    sf.write(f"{OUT}/final-voiceover.wav", final, SR, subtype="PCM_16")
    txt, words = transcribe(f"{OUT}/final-voiceover.wav", words=True)
    txt2 = transcribe(f"{OUT}/final-voiceover.wav", model=asr2)
    ref_n = norm_words(clean_text)
    idx = []
    for i, r in enumerate(flat): idx += [i] * len(norm_words(r["text"]))
    bad = set(); diffs = []; wers = {}
    for name, t in (("small.en", txt), ("medium.en", txt2)):
        hyp_n = norm_words(t); sm = difflib.SequenceMatcher(None, ref_n, hyp_n); wers[name] = round(1 - sm.ratio(), 4)
        if "".join(ref_n) == "".join(hyp_n): continue
        for tag, a1, a2, b1, b2 in sm.get_opcodes():
            if tag != "equal":
                diffs.append(dict(model=name, op=tag, script=" ".join(ref_n[a1:a2]), heard=" ".join(hyp_n[b1:b2])))
                for k in range(a1, max(a2, a1 + 1)):
                    if k < len(idx): bad.add(idx[k])
    qc["rounds"].append(dict(round=rnd, final_wer=wers, diffs=diffs, bad_phrases=sorted(bad), transcript_small=txt, transcript_medium=txt2))
    print(f"round {rnd}: diffs={diffs} bad={sorted(bad)}", flush=True)
    if not bad: break
    for i in bad:
        used = [phr[i]["seed"]]
        w, seed, tries = gen_phrase(i, banned_seeds=used)
        phr[i] = dict(w=w, seed=seed, tries=phr[i]["tries"] + tries)

# ------------------------------------------------------------- final QC -----
peak = float(np.abs(final).max()); lufs = meter.integrated_loudness(final)
clipped = int((np.abs(final) >= 0.99).sum())
# joins
starts = np.cumsum([0] + [int((d + flat[k]["pause"]) * SR) for k, d in enumerate(durs[:-1])])
d1 = np.abs(np.diff(final)); base = float(np.percentile(d1, 99.5))
join_max = []
for s in starts[1:]:
    seg = d1[max(0, s - 800):s + 800]; join_max.append(float(seg.max()) if len(seg) else 0.0)
abrupt = [round(j / base, 2) for j in join_max if j > 1.5 * base]
# pacing
rates = [len(norm_words(r["text"])) / d for r, d in zip(flat, durs)]
sec_ok = []
for si in range(len(SECTIONS)):
    zs = [(z["zone"], z["words"] / z["seconds"] if z["words"] else None, z["factor"]) for k, r in enumerate(flat) if r["sec"] == si for z in zinfo[k]]
    ms = [x[1] for x in zs if x[1]]
    ups = any(b > a * 1.04 for a, b in zip(ms, ms[1:])); downs = any(b < a * 0.96 for a, b in zip(ms, ms[1:]))
    sec_ok.append(dict(section=SECTIONS[si][0], zone_wps=[round(x, 2) for x in ms], speeds_up=ups, slows_down=downs,
                       factor_min=min(x[2] for x in zs), factor_max=max(x[2] for x in zs)))
heard_words = set(re.findall(r"[a-z]+", qc["rounds"][-1]["transcript_small"] + " " + qc["rounds"][-1]["transcript_medium"].lower()))
leaked = sorted(heard_words & CUE_WORDS)
spk = cos(REAL, emb_of(m, librosa.resample(final, orig_sr=SR, target_sr=16000)))
qc.update(dict(
    duration_s=round(len(final) / SR, 1), peak_dbfs=round(20 * np.log10(peak), 2), lufs=round(lufs, 2), ref_lufs=round(REF_LUFS, 2),
    clipped_samples=clipped, join_spikes_over_1p5x=abrupt, join_max_ratio=round(max(join_max) / base, 2),
    rate_wps=[round(x, 2) for x in rates], rate_range_pct=round((max(rates) / min(rates) - 1) * 100, 1),
    sections=sec_ok, cue_words_heard=leaked, speaker_similarity_final=round(spk, 3),
    phrases=[dict(text=flat[i]["text"], seed=phr[i]["seed"], factor=flat[i]["factor"], tries=phr[i]["tries"]) for i in range(len(flat))],
    models=dict(tts="Chatterbox Nano (110M) via ChatterboxTurboTTS(nano=True)", asr="faster-whisper small.en")))
json.dump(qc, open(f"{OUT}/qc-data.json", "w"), indent=1)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/final-voiceover.wav", "-c:a", "aac", "-b:a", "192k", f"{OUT}/final-voiceover.m4a"], check=True)
print("DONE", json.dumps({k: qc[k] for k in ["duration_s", "peak_dbfs", "lufs", "ref_lufs", "clipped_samples", "join_max_ratio", "rate_range_pct", "cue_words_heard", "speaker_similarity_final"]}), flush=True)
