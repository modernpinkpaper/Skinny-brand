"""The voice: Chatterbox copies the voice in a short sample; the script is said a paragraph at a time
so it flows, then cut at each line end. Whisper gives the time of every spoken word, which is used both
to cut the lines and to pop each caption word in exactly when it is said."""
import os, re, difflib, subprocess, tempfile
import numpy as np, soundfile as sf, imageio_ffmpeg
from .paths import device
from .direct import FEELS, PACES

SR, FPS = 24000, 30
FRAME = SR // FPS                 # samples per video frame: cuts land on frame edges so nothing drifts
PAUSE, EXTRA_PAUSE, CHUNK_CHARS = 0.35, 0.6, 260   # 1 blank line = PAUSE s, each extra blank line adds EXTRA_PAUSE s
LEAN_SPEED, LEAN_LOUD, LEAN_BEAT = 0.8, 1.6, 0.08   # a *word*: said this much slower and louder, after a tiny breath
FF = imageio_ffmpeg.get_ffmpeg_exe()
NOWIN = 0x08000000 if os.name == "nt" else 0

_tts = None
def speak(text, ref, speed=1.0, feel="normal"):
    """speed < 1 is slower. Chatterbox is asked for calm pacing (more or less emotion for the feeling), then
    the audio is gently slowed (pitch stays the same) if a slower speed was chosen."""
    global _tts
    import torchaudio
    if _tts is None:
        from chatterbox.tts import ChatterboxTTS
        _tts = ChatterboxTTS.from_pretrained(device=device())
    ex, cfg, _ = FEELS.get(feel, FEELS["normal"])
    w = _tts.generate(text, audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg)
    if _tts.sr != SR: w = torchaudio.functional.resample(w, _tts.sr, SR)
    a = w.squeeze(0).cpu().numpy().astype(np.float32)
    return stretch(a, speed) if abs(speed - 1.0) > 0.01 else a


def stretch(a, speed):
    d = tempfile.mkdtemp(); i, o = os.path.join(d, "i.wav"), os.path.join(d, "o.wav")
    sf.write(i, a, SR)
    subprocess.run([FF, "-loglevel", "error", "-y", "-i", i, "-filter:a", f"atempo={speed:.3f}", o],
                   check=True, creationflags=NOWIN)
    b, _ = sf.read(o, dtype="float32")
    return b


def trim(a, thr=0.01, keep=0.04):
    loud = np.where(np.abs(a) > thr)[0]
    if not len(loud): return a
    k = int(keep * SR); return a[max(loud[0] - k, 0):loud[-1] + k]


def clean(a):
    """Removes the faint hiss the copied voice has while talking, so talking and pauses sound the same."""
    import noisereduce as nr
    return nr.reduce_noise(y=a, sr=SR, stationary=True, prop_decrease=0.85).astype(np.float32)


def _lean(a, wt, d):
    """Leans on word d: says it a bit slower and louder. Returns (audio, seconds added)."""
    s0, e0 = int(max(wt[d][0] - 0.02, 0) * SR), int(min(wt[d][1] + 0.02, len(a) / SR) * SR)
    if e0 - s0 < int(0.08 * SR): return a, 0.0
    seg = stretch(a[s0:e0], LEAN_SPEED).astype(np.float32)
    ramp = int(0.03 * SR); gain = np.full(len(seg), LEAN_LOUD, np.float32)
    gain[:ramp] = np.linspace(1, LEAN_LOUD, ramp); gain[-ramp:] = np.linspace(LEAN_LOUD, 1, ramp)
    seg = np.tanh(seg * gain * 1.1) / 1.1   # louder, and gently rounded off instead of clipping
    fade = int(0.004 * SR)   # tiny fades so the joins don't click
    seg[:fade] *= np.linspace(0, 1, fade); seg[-fade:] *= np.linspace(1, 0, fade)
    beat = np.zeros(int(LEAN_BEAT * SR) if s0 > 0 else 0, np.float32)
    return np.concatenate([a[:s0], beat, seg, a[e0:]]), (len(beat) + len(seg) - (e0 - s0)) / SR


def _direct(a, wt, g, dirs):
    """Applies the *word* and (pause) marks of the lines in group g: changes the audio and moves the word times."""
    marks, d = [], 0   # (time, kind, word number in the group, value)
    for k in g:
        n = len(dirs[k]["line_words"])
        for j in sorted(dirs[k]["emph"]):
            if j < n: marks.append((wt[d + j][0], "lean", d + j, 0))
        for j, sec in dirs[k]["pauses"].items():
            if j < 0: t = max(wt[d][0] - 0.03, 0.0)
            elif d + j + 1 < len(wt): t = (wt[d + j][1] + wt[d + j + 1][0]) / 2
            else: t = min(wt[d + j][1] + 0.03, len(a) / SR)
            marks.append((t, "pause", d + j, sec))
        d += n
    wt = list(wt)
    for t, kind, w, val in sorted(marks, key=lambda m: -m[0]):   # last first, so earlier times stay right
        if kind == "lean":
            a, add = _lean(a, wt, w)
            if add:
                b = LEAN_BEAT if wt[w][0] > 0.02 else 0.0   # the word itself starts after the breath
                wt = wt[:w] + [(wt[w][0] + b, wt[w][1] + add)] + [(x + add, y + add) for x, y in wt[w + 1:]]
        else:
            i = int(t * SR); a = np.concatenate([a[:i], np.zeros(int(val * SR), np.float32), a[i:]])
            wt = [(x + val, y + val) if x >= t else (x, y) for x, y in wt]
    return a, wt


def _norm(t): return "".join(re.findall(r"[a-z0-9]+", t.lower().replace("'", "").replace("’", "")))


_wm = None
def voice_lines(lines, breaks, ref, speed=1.0, progress=lambda *a: None, dirs=None):
    """breaks: {line number: blank lines after it}. dirs: voice marks per line from direct.parse() (or None).
    Returns (pieces, times): one audio piece per line, and for each line the (start, end) seconds of every word
    of line.split(), measured from the start of its piece."""
    global _wm
    breaks = {int(k): v for k, v in breaks.items()}
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    if not dirs or len(dirs) != len(lines): dirs = [dict(feel="normal", pace="normal", emph=set(), pauses={})] * len(lines)
    dirs = [dict(d, line_words=l.split()) for d, l in zip(dirs, lines)]
    how = lambda i: (dirs[i]["feel"], dirs[i]["pace"])
    groups, cur = [], []
    for i, l in enumerate(lines):
        cur.append(i)
        long = len(" ".join(lines[j] for j in cur)) > CHUNK_CHARS - 60 and l.rstrip().endswith((".", "!", "?", "…"))
        change = i + 1 < len(lines) and how(i + 1) != how(i)   # a new feeling or speed is said separately
        if i in breaks or long or change or i == len(lines) - 1: groups.append(cur); cur = []
    pieces, times = [], []
    for n, g in enumerate(groups):
        progress(n / len(groups), f"voice: part {n + 1} of {len(groups)}")
        feel, pace = how(g[0])
        a = clean(trim(speak(" ".join(lines[i] for i in g), ref, speed * PACES[pace] * FEELS[feel][2], feel)))
        a16 = np.interp(np.arange(0, len(a), SR / 16000), np.arange(len(a)), a).astype(np.float32)
        spoken = [w for seg in _wm.transcribe(a16, word_timestamps=True)[0] for w in seg.words]
        # line up the script's words with the words Whisper heard
        disp = [(k, w) for k in g for w in lines[k].split()]
        match = {}
        for b in difflib.SequenceMatcher(None, [_norm(w) for _, w in disp], [_norm(w.word) for w in spoken],
                                         autojunk=False).get_matching_blocks():
            for x in range(b.size): match[b.a + x] = b.b + x
        total = len(a) / SR; wt = []
        for d in range(len(disp)):   # time of every script word; words Whisper missed are spread in between
            if d in match: wt.append((spoken[match[d]].start, spoken[match[d]].end)); continue
            prev = max([x for x in match if x < d], default=None); nxt = min([x for x in match if x > d], default=None)
            t0 = spoken[match[prev]].end if prev is not None else 0.0
            t1 = spoken[match[nxt]].start if nxt is not None else total
            gap_prev = d - (prev if prev is not None else -1); span = (nxt if nxt is not None else len(disp)) - (prev if prev is not None else -1)
            s = t0 + (t1 - t0) * (gap_prev - 1) / span; wt.append((s, s + (t1 - t0) / span))
        a, wt = _direct(a, wt, g, dirs); total = len(a) / SR
        cuts, idx = [], 0
        for k in g[:-1]:   # cut between a line's last word and the next line's first word
            idx += len(lines[k].split())
            c = (wt[idx - 1][1] + wt[idx][0]) / 2 if 0 < idx < len(wt) else total * idx / max(len(disp), 1)
            cuts.append(int(round(c * SR / FRAME)) * FRAME)
        pause = PAUSE + EXTRA_PAUSE * (breaks.get(g[-1], 1) - 1) if g[-1] in breaks else 0
        if pause: a = np.concatenate([a, np.zeros(int(pause * SR), np.float32)])
        a = np.concatenate([a, np.zeros(-len(a) % FRAME, np.float32)])
        edges = [0]
        for c in cuts: edges.append(min(max(c, edges[-1] + FRAME), len(a) - FRAME * (len(g) - len(edges))))
        edges.append(len(a))
        idx = 0
        for n2, k in enumerate(g):
            pieces.append(a[edges[n2]:edges[n2 + 1]]); off = edges[n2] / SR; m = len(lines[k].split())
            times.append([(max(0.0, s - off), max(0.0, e - off)) for s, e in wt[idx:idx + m]]); idx += m
    return pieces, times
