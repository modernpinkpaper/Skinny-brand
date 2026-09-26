#!/usr/bin/env python3
"""Clip-compilation video with a free AI voiceover (Kokoro, runs offline).
Each script line gets one short clip; the line is typed on screen while the voice says it,
and the clip lasts exactly as long as the voice line (+ a small pause).

Folder needs: script.py (LINES = [(line, search)], END = "...") and clips.txt (one clip URL per line).
Usage: python3 clip-videos/make_video.py clip-videos/doesnt-count [--voice af_heart] [--speed 1.0]
       python3 clip-videos/make_video.py clip-videos/doesnt-count --clone clip-videos/voices/guy-ref.wav --out doesnt-count-guy-voice.mp4
       add --flow so a sentence split over several lines is spoken in one breath instead of stopping after every line
Output: <folder>/<folder-name>.mp4 and <folder>/voiceover.wav"""
import os, re, sys, argparse, importlib.util, subprocess, tempfile, textwrap, requests, imageio_ffmpeg
import numpy as np, soundfile as sf
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motion_check import score as motion_score

ap = argparse.ArgumentParser()
ap.add_argument("folder"); ap.add_argument("--voice", default="af_heart"); ap.add_argument("--speed", type=float, default=1.0)
ap.add_argument("--clone", help="10-15s wav of a voice (used with permission) to copy with Chatterbox instead of Kokoro")
ap.add_argument("--out", help="output file name (default: <folder-name>.mp4)")
ap.add_argument("--grade", choices=["moody"], help="colour-grade every clip the same way (moody = darker, softer colours)")
ap.add_argument("--flow", action="store_true",
                help="say the script a paragraph at a time (so the voice flows across lines and sentences), then cut it at the line ends")
args = ap.parse_args()
HERE = os.path.abspath(args.folder)
ROOT = os.path.dirname(os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location("script", os.path.join(HERE, "script.py"))
script = importlib.util.module_from_spec(spec); spec.loader.exec_module(script)
LINES, END = script.LINES, script.END
BREAKS = set(getattr(script, "BREAKS", []))   # line numbers followed by a blank line in the script (pause there)
CLIPS = [l.strip() for l in open(os.path.join(HERE, "clips.txt")) if l.strip() and not l.startswith("#")]
assert len(CLIPS) == len(LINES), (len(CLIPS), len(LINES))

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS, SR = 1080, 1920, 30, 24000
PAUSE, END_HOLD, MIN_LEN = 0.4, 2.5, 1.3   # silence after each line, extra end-screen time, shortest clip
tmp = tempfile.mkdtemp()

# ---- voice ----
if args.clone:
    # Chatterbox (MIT license) copies the voice in the reference clip. Slow on CPU: ~6s per 1s of speech.
    import torch, torchaudio
    from chatterbox.tts import ChatterboxTTS
    cb = ChatterboxTTS.from_pretrained(device="cpu")
    def speak(text):
        w = cb.generate(text, audio_prompt_path=os.path.abspath(args.clone), exaggeration=0.4, cfg_weight=0.5)
        if cb.sr != SR: w = torchaudio.functional.resample(w, cb.sr, SR)
        return w.squeeze(0).numpy().astype(np.float32)
else:
    # Kokoro (free, offline). Model is downloaded once to ~/.cache/kokoro
    from kokoro_onnx import Kokoro
    MD = os.path.expanduser("~/.cache/kokoro"); os.makedirs(MD, exist_ok=True)
    for f in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:
        if not os.path.exists(os.path.join(MD, f)):
            subprocess.run(["curl", "-sL", "-C", "-", "-o", os.path.join(MD, f),
                            f"https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/{f}"], check=True)
    tts = Kokoro(os.path.join(MD, "kokoro-v1.0.onnx"), os.path.join(MD, "voices-v1.0.bin"))
    def speak(text):
        a, sr = tts.create(text, voice=args.voice, speed=args.speed, lang="en-us")
        assert sr == SR; return a.astype(np.float32)

def trim(a, thr=0.01, keep=0.04):
    """Cuts the silence the voice leaves at the start and end."""
    loud = np.where(np.abs(a) > thr)[0]
    if not len(loud): return a
    k = int(keep * SR); return a[max(loud[0] - k, 0):loud[-1] + k]

SENT_PAUSE, FRAME = 0.35, SR // FPS   # pause at a paragraph break in --flow mode; samples per video frame
CHUNK_CHARS = 260                     # longest stretch of script the voice says in one go

def clean(a):
    """Removes the faint hiss the cloned voice has while talking, so talking and pauses sound the same."""
    import noisereduce as nr
    return nr.reduce_noise(y=a, sr=SR, stationary=True, prop_decrease=0.85).astype(np.float32)

def words_of(t): return re.findall(r"[a-z0-9]+", t.lower().replace("'", ""))

def flow_audio(lines, breaks):
    """Speaks the script a paragraph at a time (so it flows across lines AND sentences), then cuts it at
    each line end, found by lining up the script's words with Whisper's word timings.
    Returns one audio piece per line. Only a paragraph break (blank line in the script) adds a pause.
    Cuts land on video-frame edges so the clips and the voice never drift apart."""
    import difflib
    from faster_whisper import WhisperModel
    wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    groups, cur = [], []
    for i, l in enumerate(lines):
        cur.append(l)
        long = len(" ".join(cur)) > CHUNK_CHARS - 60 and l.rstrip().endswith((".", "!", "?", "…"))
        if i in breaks or long or i == len(lines) - 1: groups.append((cur, i in breaks)); cur = []
    out = []
    for g, pause in groups:
        a = clean(trim(speak(" ".join(g))))
        a16 = np.interp(np.arange(0, len(a), SR / 16000), np.arange(len(a)), a).astype(np.float32)
        spoken = [w for seg in wm.transcribe(a16, word_timestamps=True)[0] for w in seg.words]
        sw = [(words_of(w.word) or [""])[0] for w in spoken]
        script_words, line_end = [], []
        for l in g: script_words += words_of(l); line_end.append(len(script_words) - 1)
        match = {}
        for b in difflib.SequenceMatcher(None, script_words, sw, autojunk=False).get_matching_blocks():
            for k in range(b.size): match[b.a + k] = b.b + k
        cuts = []
        for n, e in enumerate(line_end[:-1]):
            k = max([x for x in match if x <= e], default=None)
            if k is None or match[k] + 1 >= len(spoken):   # no match: split by share of letters
                c = len(a) / SR * (e + 1) / len(script_words)
            else:
                j = match[k] + (e - k); j = min(j, len(spoken) - 2)
                c = (spoken[j].end + spoken[j + 1].start) / 2
            cuts.append(int(round(c * SR / FRAME)) * FRAME)
        if pause: a = np.concatenate([a, np.zeros(int(SENT_PAUSE * SR), np.float32)])
        a = np.concatenate([a, np.zeros(-len(a) % FRAME, np.float32)])
        edges = [0]
        for c in cuts: edges.append(min(max(c, edges[-1] + FRAME), len(a) - FRAME * (len(g) - len(edges))))
        edges.append(len(a))
        out += [a[edges[k]:edges[k + 1]] for k in range(len(g))]
    return out

# ---- text overlays ----
def font(name, weight, size):
    ttf = os.path.join(tmp, name + ".ttf")
    if not os.path.exists(ttf):
        f = TTFont(os.path.join(ROOT, "brand/fonts", name + ".woff2")); f.flavor = None; f.save(ttf)
    ft = ImageFont.truetype(ttf, size); ft.set_variation_by_axes([weight]); return ft
SERIF = font("Lora-normal", 700, 66)
SANS = font("Inter-normal", 600, 86)

def text_layer(text, fnt, cy, shadow=True, width=24):
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width) or [""]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lh = int(fnt.size * 1.08); y0 = cy - lh * len(lines) // 2
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        for i, l in enumerate(lines):
            sd.text((W // 2 + 3, y0 + i * lh + 4), l, font=fnt, fill=(0, 0, 0, 255), anchor="ma")
        sh = sh.filter(ImageFilter.GaussianBlur(7)); im = Image.alpha_composite(im, sh)
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(2)))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((W // 2, y0 + i * lh), l, font=fnt, fill="white", anchor="ma")
    return im

def typed_overlay(text, fnt, cy, type_time, dur, out, shadow=True, width=24):
    """Types the text over `type_time` seconds (in step with the voice), then holds until `dur`."""
    step = type_time / len(text); steps = [(text[:n] + "|", step) for n in range(1, len(text) + 1)]
    steps.append((text + "|", max(dur - type_time, 0.05)))
    lst = []
    for k, (s, d) in enumerate(steps):
        p = f"{out}_{k:03d}.png"; text_layer(s, fnt, cy, shadow, width).save(p)
        lst.append(f"file '{p}'\nduration {d:.4f}\n")
    lst.append(f"file '{p}'\n"); open(out + ".txt", "w").write("".join(lst))
    return out + ".txt"

# ---- build ----
sess = requests.Session(); sess.headers["User-Agent"] = "Mozilla/5.0"
parts, audio, stills = [], [], []
flow = flow_audio([l for l, _ in LINES], BREAKS) if args.flow else None
for i, ((line, _), url) in enumerate(zip(LINES, CLIPS)):
    src = os.path.join(HERE, "clips", f"{i:02d}.mp4"); os.makedirs(os.path.dirname(src), exist_ok=True)
    if not os.path.exists(src): open(src, "wb").write(sess.get(url).content)
    if motion_score(src)[1] < 1.5: stills.append(f"{i:02d} {line}")
    if flow is not None:   # already includes its pause; speech time = piece minus the trailing silence
        piece = flow[i]; dur = len(piece) / SR; audio.append(piece); a = trim(piece, keep=0)
    else:
        a = speak(line); dur = max(len(a) / SR + PAUSE, MIN_LEN)
        audio.append(np.concatenate([a, np.zeros(int(round(dur * SR)) - len(a), np.float32)]))
    ov = typed_overlay(line, SERIF, 1010, len(a) / SR * 0.85, dur, os.path.join(tmp, f"t{i}"))
    out = os.path.join(tmp, f"p{i:02d}.mp4")
    grade = "eq=saturation=0.72:brightness=-0.035:contrast=1.06:gamma=0.95,vignette=PI/5," if args.grade == "moody" else ""
    vf = (f"[0:v]{grade}scale={W}:1250:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2-60:color=0x080808,fps={FPS},setsar=1[v];"
          f"[1:v]fps={FPS}[t];[v][t]overlay=0:0:shortest=1,format=yuv420p")
    subprocess.run([FF, "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", src, "-f", "concat", "-safe", "0",
                    "-i", ov, "-t", f"{dur:.3f}", "-filter_complex", vf, "-an", "-c:v", "libx264", "-crf", "18",
                    "-r", str(FPS), out], check=True)
    parts.append(out); print(f"{i:02d} {dur:4.1f}s  {line}", flush=True)

a = speak(END)
if args.flow: a = clean(trim(a))
end_dur = len(a) / SR + END_HOLD
audio.append(np.concatenate([a, np.zeros(int(round(end_dur * SR)) - len(a), np.float32)]))
bg = os.path.join(tmp, "bg.png"); Image.new("RGB", (W, H), (22, 22, 22)).save(bg)
ov = typed_overlay(END, SANS, 900, len(a) / SR * 0.85, end_dur, os.path.join(tmp, "end"), shadow=False, width=22)
out = os.path.join(tmp, "p_end.mp4")
subprocess.run([FF, "-loglevel", "error", "-y", "-loop", "1", "-i", bg, "-f", "concat", "-safe", "0", "-i", ov,
                "-t", f"{end_dur:.3f}", "-filter_complex", f"[1:v]fps={FPS}[t];[0:v][t]overlay=0:0,format=yuv420p",
                "-c:v", "libx264", "-crf", "18", "-r", str(FPS), out], check=True)
parts.append(out)

wav = os.path.join(HERE, (args.out or "x").replace(".mp4", "") + "-voiceover.wav" if args.out else "voiceover.wav"); sf.write(wav, np.concatenate(audio), SR)
lst = os.path.join(tmp, "all.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
final = os.path.join(HERE, args.out or os.path.basename(HERE) + ".mp4")
subprocess.run([FF, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
                "-movflags", "+faststart", final], check=True)
print("saved", final)
if stills: print("WARNING - these clips barely move (still image / zoom effect), swap them:\n  " + "\n  ".join(stills))
