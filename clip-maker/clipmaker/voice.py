"""The voice: Chatterbox copies the voice in a short sample; the script is said a paragraph at a time
so it flows, then cut at each line end using Whisper's word timings."""
import re, difflib
import numpy as np
from .paths import device

SR, FPS = 24000, 30
FRAME = SR // FPS                 # samples per video frame: cuts land on frame edges so nothing drifts
PARA_PAUSE, CHUNK_CHARS = 0.35, 260

_tts = None
def speak(text, ref):
    global _tts
    import torchaudio
    if _tts is None:
        from chatterbox.tts import ChatterboxTTS
        _tts = ChatterboxTTS.from_pretrained(device=device())
    w = _tts.generate(text, audio_prompt_path=ref, exaggeration=0.4, cfg_weight=0.5)
    if _tts.sr != SR: w = torchaudio.functional.resample(w, _tts.sr, SR)
    return w.squeeze(0).cpu().numpy().astype(np.float32)


def trim(a, thr=0.01, keep=0.04):
    loud = np.where(np.abs(a) > thr)[0]
    if not len(loud): return a
    k = int(keep * SR); return a[max(loud[0] - k, 0):loud[-1] + k]


def clean(a):
    """Removes the faint hiss the copied voice has while talking, so talking and pauses sound the same."""
    import noisereduce as nr
    return nr.reduce_noise(y=a, sr=SR, stationary=True, prop_decrease=0.85).astype(np.float32)


def _words(t): return re.findall(r"[a-z0-9]+", t.lower().replace("'", "").replace("’", ""))


_wm = None
def voice_lines(lines, breaks, ref, progress=lambda *a: None):
    """Returns one audio piece per line (a pause only after a paragraph break)."""
    global _wm
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    groups, cur = [], []
    for i, l in enumerate(lines):
        cur.append(l)
        long = len(" ".join(cur)) > CHUNK_CHARS - 60 and l.rstrip().endswith((".", "!", "?", "…"))
        if i in breaks or long or i == len(lines) - 1: groups.append((cur, i in breaks)); cur = []
    out = []
    for n, (g, pause) in enumerate(groups):
        progress(n / len(groups), f"voice: part {n + 1} of {len(groups)}")
        a = clean(trim(speak(" ".join(g), ref)))
        a16 = np.interp(np.arange(0, len(a), SR / 16000), np.arange(len(a)), a).astype(np.float32)
        spoken = [w for seg in _wm.transcribe(a16, word_timestamps=True)[0] for w in seg.words]
        sw = [(_words(w.word) or [""])[0] for w in spoken]
        script_words, line_end = [], []
        for l in g: script_words += _words(l); line_end.append(len(script_words) - 1)
        match = {}
        for b in difflib.SequenceMatcher(None, script_words, sw, autojunk=False).get_matching_blocks():
            for k in range(b.size): match[b.a + k] = b.b + k
        cuts = []
        for e in line_end[:-1]:
            k = max([x for x in match if x <= e], default=None)
            if k is None or match[k] + 1 >= len(spoken):
                c = len(a) / SR * (e + 1) / max(len(script_words), 1)
            else:
                j = min(match[k] + (e - k), len(spoken) - 2)
                c = (spoken[j].end + spoken[j + 1].start) / 2
            cuts.append(int(round(c * SR / FRAME)) * FRAME)
        if pause: a = np.concatenate([a, np.zeros(int(PARA_PAUSE * SR), np.float32)])
        a = np.concatenate([a, np.zeros(-len(a) % FRAME, np.float32)])
        edges = [0]
        for c in cuts: edges.append(min(max(c, edges[-1] + FRAME), len(a) - FRAME * (len(g) - len(edges))))
        edges.append(len(a))
        out += [a[edges[k]:edges[k + 1]] for k in range(len(g))]
    return out
