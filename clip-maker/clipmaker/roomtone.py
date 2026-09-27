"""Room tone: the copied voice has a faint, steady background hiss while it talks, but the pauses between
sentences are dead silent, so the hiss cuts out abruptly. This lays the voice's own hiss (taken from the
quietest moments between its words) under the whole track, so the background never stops.
Only needs numpy, so clip-videos/make_video.py can use it too."""
import numpy as np


def fill(a, sr):
    """a: the whole voiceover (float32, mono). Returns it with the silent gaps filled by its own hiss."""
    F = int(0.02 * sr)                                      # 20 ms frames
    fr = a[:len(a) // F * F].reshape(-1, F)
    rms = np.sqrt((fr ** 2).mean(1)); live = rms > 1e-5     # frames that aren't dead silent
    if not live.any(): return a
    # the quietest 10% of the voice is the hiss between words (skipping near-silent bits at the gap edges)
    noise = fr[(rms > 10 ** (-50 / 20)) & (rms <= np.percentile(rms[live], 10))].ravel()
    if len(noise) < 0.2 * sr: return a                     # no hiss to copy (e.g. a clean Kokoro voice)
    # a bed as long as the track: random half-second chunks overlapped with crossfades so it never loops audibly
    L, X = int(0.5 * sr), int(0.1 * sr); rng = np.random.default_rng(0)
    win = np.ones(L, np.float32); win[:X] = np.linspace(0, 1, X); win[-X:] = np.linspace(1, 0, X)
    src = np.tile(noise, int(np.ceil(2 * L / len(noise))) + 1)
    bed = np.zeros(len(a) + L, np.float32)
    for s in range(0, len(a), L - X):
        o = rng.integers(0, len(src) - L); bed[s:s + L] += src[o:o + L] * win
    # full bed in the gaps (fading in over 60 ms), 35% under the talking (the voice already has its own hiss there)
    talk = np.concatenate([np.repeat(live, F), np.zeros(len(a) - len(fr) * F, bool)]).astype(np.float32)
    k = int(0.06 * sr); talk = np.convolve(talk, np.ones(k) / k, "same")
    return (a + bed[:len(a)] * np.clip(1 - talk, 0.35, 1)).astype(np.float32)
