#!/usr/bin/env python3
"""Builds the clip-compilation video: one short famous clip per script line, with the line
typed out letter by letter (white bold serif + soft shadow), then a plain share screen.
Usage: python3 clip-videos/night-snacking/render.py      -> clip-videos/night-snacking/night-snacking.mp4"""
import os, subprocess, tempfile, textwrap, requests, imageio_ffmpeg
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from script import LINES, END

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS = 1080, 1920, 30
CPS, HOLD, MIN_LEN = 17, 0.9, 2.0          # typing speed (chars/sec), pause after a line, shortest clip
BG = (8, 8, 8)

# Tenor clip picked for each line (same order as LINES)
CLIPS = [l.strip() for l in open(os.path.join(HERE, "clips.txt")) if l.strip() and not l.startswith("#")]
assert len(CLIPS) == len(LINES), (len(CLIPS), len(LINES))

tmp = tempfile.mkdtemp()
def font(name, weight, size):
    ttf = os.path.join(tmp, name + ".ttf")
    if not os.path.exists(ttf):
        f = TTFont(os.path.join(ROOT, "brand/fonts", name + ".woff2")); f.flavor = None; f.save(ttf)
    ft = ImageFont.truetype(ttf, size); ft.set_variation_by_axes([weight]); return ft
SERIF = font("Lora-normal", 700, 66)
SANS = font("Inter-normal", 600, 86)

def text_layer(text, fnt, cy, shadow=True, width=24):
    """Transparent 1080x1920 PNG with centered text (plus typing cursor)."""
    lines = []
    for para in text.split("\n"):
        lines += textwrap.wrap(para, width) or [""]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
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

def typed_overlay(text, fnt, cy, dur, out, shadow=True, width=24):
    """Overlay video (PNG frames via concat) that types the text then holds."""
    steps, t = [], 0.0
    for n in range(1, len(text) + 1):
        steps.append((text[:n] + "|", 1 / CPS)); t += 1 / CPS
    steps.append((text + "|", max(dur - t, 0.1)))
    lst = []
    for k, (s, d) in enumerate(steps):
        p = f"{out}_{k:03d}.png"; text_layer(s, fnt, cy, shadow, width).save(p)
        lst.append(f"file '{p}'\nduration {d:.4f}\n")
    lst.append(f"file '{p}'\n")
    open(out + ".txt", "w").write("".join(lst))
    return out + ".txt"

def clip_len(text): return max(MIN_LEN, len(text) / CPS + HOLD)

sess = requests.Session(); sess.headers["User-Agent"] = "Mozilla/5.0"
parts = []
for i, ((line, _), url) in enumerate(zip(LINES, CLIPS)):
    src = os.path.join(HERE, "clips", f"{i:02d}.mp4")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    if not os.path.exists(src): open(src, "wb").write(sess.get(url).content)
    dur = clip_len(line)
    ov = typed_overlay(line, SERIF, 1010, dur, os.path.join(tmp, f"t{i}"))
    out = os.path.join(tmp, f"p{i:02d}.mp4")
    # clip fills the width (max 1250 tall), sits a bit above center on black; text sits on its lower half
    vf = (f"[0:v]scale={W}:1250:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2,"
          f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2-60:color=0x080808,fps={FPS},setsar=1[v];"
          f"[1:v]fps={FPS}[t];[v][t]overlay=0:0:shortest=1,format=yuv420p")
    subprocess.run([FF, "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", src,
                    "-f", "concat", "-safe", "0", "-i", ov, "-t", f"{dur:.3f}",
                    "-filter_complex", vf, "-an", "-c:v", "libx264", "-crf", "18", "-r", str(FPS), out], check=True)
    parts.append(out); print(f"{i:02d} {dur:.1f}s  {line}")

# end screen: dark, plain sans text typed out, like the original
end_dur = 7.0
bg = os.path.join(tmp, "bg.png"); Image.new("RGB", (W, H), (22, 22, 22)).save(bg)
ov = typed_overlay(END, SANS, 900, end_dur, os.path.join(tmp, "end"), shadow=False, width=24)
out = os.path.join(tmp, "p_end.mp4")
subprocess.run([FF, "-loglevel", "error", "-y", "-loop", "1", "-i", bg, "-f", "concat", "-safe", "0", "-i", ov,
                "-t", f"{end_dur}", "-filter_complex", f"[1:v]fps={FPS}[t];[0:v][t]overlay=0:0,format=yuv420p",
                "-c:v", "libx264", "-crf", "18", "-r", str(FPS), out], check=True)
parts.append(out)

lst = os.path.join(tmp, "all.txt"); open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
final = os.path.join(HERE, "night-snacking.mp4")
subprocess.run([FF, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
                "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart", final], check=True)
print("saved", final)
