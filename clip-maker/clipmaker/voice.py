"""The voice: Chatterbox copies the voice in a short sample; the script is said a paragraph at a time
so it flows, then cut at each line end. Whisper gives the time of every spoken word, which is used both
to cut the lines and to pop each caption word in exactly when it is said."""
import os, re, difflib, subprocess, tempfile
import numpy as np, soundfile as sf, imageio_ffmpeg
from .paths import device

SR, FPS = 24000, 30
FRAME = SR // FPS                 # samples per video frame: cuts land on frame edges so nothing drifts
PAUSE, EXTRA_PAUSE, CHUNK_CHARS = 0.35, 0.6, 260   # 1 blank line = PAUSE s, each extra blank line adds EXTRA_PAUSE s
FF = imageio_ffmpeg.get_ffmpeg_exe()
NOWIN = 0x08000000 if os.name == "nt" else 0

_tts = None
def speak(text, ref, speed=1.0):
    """speed < 1 is slower. Chatterbox is asked for calm pacing, then the audio is gently slowed
    (pitch stays the same) if a slower speed was chosen."""
    global _tts
    import torchaudio
    if _tts is None:
        from chatterbox.tts import ChatterboxTTS
        _tts = ChatterboxTTS.from_pretrained(device=device())
    w = _tts.generate(text, audio_prompt_path=ref, exaggeration=0.4, cfg_weight=0.35)
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


def _norm(t): return "".join(re.findall(r"[a-z0-9]+", t.lower().replace("'", "").replace("’", "")))


_wm = None
def voice_lines(lines, breaks, ref, speed=1.0, progress=lambda *a: None):
    """breaks: {line number: blank lines after it}. Returns (pieces, times): one audio piece per line, and for
    each line the (start, end) seconds of every word of line.split(), measured from the start of its piece."""
    global _wm
    breaks = {int(k): v for k, v in breaks.items()}
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    groups, cur = [], []
    for i, l in enumerate(lines):
        cur.append(i)
        long = len(" ".join(lines[j] for j in cur)) > CHUNK_CHARS - 60 and l.rstrip().endswith((".", "!", "?", "…"))
        if i in breaks or long or i == len(lines) - 1: groups.append(cur); cur = []
    pieces, times = [], []
    for n, g in enumerate(groups):
        progress(n / len(groups), f"voice: part {n + 1} of {len(groups)}")
        a = clean(trim(speak(" ".join(lines[i] for i in g), ref, speed)))
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
