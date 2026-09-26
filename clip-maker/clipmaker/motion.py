#!/usr/bin/env python3
"""Scores how much a clip really moves, to reject still images (and stills with a zoom/pan effect).
motion = how much the picture changes frame to frame; a still scores ~0.
For a zoom/pan on a still, a frame is almost exactly a scaled/shifted copy of the one before,
so after lining frames up (best shift+scale) nearly nothing is left ("true motion" ~0).
Usage: python3 clip-videos/motion_check.py clip1.mp4 clip2.mp4 ...   (prints scores, flags STILL)"""
import os, sys, subprocess, numpy as np, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe(); N = 96

def frames(path, fps=6):
    raw = subprocess.run([FF, "-loglevel", "error", "-i", path, "-vf", f"fps={fps},scale={N}:{N},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, creationflags=0x08000000 if os.name == "nt" else 0).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, N, N).astype(np.float32)

def best_aligned_diff(a, b):
    """Smallest difference between b and a slightly zoomed/shifted a (catches Ken Burns effects)."""
    best = np.abs(a - b)[8:-8, 8:-8].mean()
    for s in (0.97, 0.985, 1.0, 1.015, 1.03):
        m = int(N * s); ys = (np.arange(N) * N / m).clip(0, N - 1).astype(int)
        z = a[np.ix_(ys, ys)] if s != 1 else a
        c = (z.shape[0] - N) // 2 if s > 1 else 0
        for dy in (-2, 0, 2):
            for dx in (-2, 0, 2):
                zz = np.roll(np.roll(z, dy, 0), dx, 1)[:N, :N]
                best = min(best, np.abs(zz - b)[8:-8, 8:-8].mean())
    return best

def score(path):
    f = frames(path)
    if len(f) < 3: return 0.0, 0.0
    raw = np.mean([np.abs(f[i + 1] - f[i]).mean() for i in range(len(f) - 1)])
    true = np.mean([best_aligned_diff(f[i], f[i + 1]) for i in range(len(f) - 1)])
    return raw, true

if __name__ == "__main__":
    for p in sys.argv[1:]:
        raw, true = score(p)
        print(f"{p}: motion {raw:5.1f}  true-motion {true:5.1f}  {'STILL/EFFECT' if true < 1.5 else ''}")


def cuts(path, fps=10):
    """How many hard cuts (jumps to a different shot) a clip has. A clip made of lots of mini-clips has several;
    one continuous shot has none. A cut = the picture's layout changes completely from one frame to the next
    (low correlation), so fades, flashes and fast movement inside one shot don't count."""
    raw = subprocess.run([FF, "-loglevel", "error", "-i", path, "-vf", f"fps={fps},scale=48:48,format=gray",
                          "-f", "rawvideo", "-"], capture_output=True,
                         creationflags=0x08000000 if os.name == "nt" else 0).stdout
    f = np.frombuffer(raw, np.uint8).reshape(-1, 48 * 48).astype(np.float32)
    if len(f) < 3: return 0
    n, last = 0, -9
    for i in range(len(f) - 1):
        a, b = f[i] - f[i].mean(), f[i + 1] - f[i + 1].mean()
        if a.std() < 4 or b.std() < 4: continue          # (nearly) blank frame, e.g. fading from black
        corr = float((a * b).mean() / (a.std() * b.std()))
        if corr < 0.45 and np.abs(f[i + 1] - f[i]).mean() > 18 and i - last > 2:
            n += 1; last = i
    return n
