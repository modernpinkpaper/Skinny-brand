"""Puts it together: each clip on a dark 9:16 frame, colour-graded, the line typed on screen while the
voice says it, then an end screen. Saves <project>/<name>.mp4, the voiceover .wav and caption.txt."""
import os, subprocess, tempfile, textwrap, shutil
import numpy as np, soundfile as sf, imageio_ffmpeg
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .paths import ASSETS
from .sources import S
from .looks import LOOKS
from . import voice

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS, SR = 1080, 1920, 30, voice.SR
END_HOLD = 2.5
NOWIN = 0x08000000 if os.name == "nt" else 0   # no black console windows popping up on Windows


def _run(cmd): subprocess.run(cmd, check=True, creationflags=NOWIN)


def _font(tmp, name, weight, size):
    ttf = os.path.join(tmp, name + ".ttf")
    if not os.path.exists(ttf):
        f = TTFont(os.path.join(ASSETS, "fonts", name + ".woff2")); f.flavor = None; f.save(ttf)
    ft = ImageFont.truetype(ttf, size); ft.set_variation_by_axes([weight]); return ft


def _text_layer(text, fnt, cy, shadow=True, width=24):
    lines = []
    for para in text.split("\n"): lines += textwrap.wrap(para, width) or [""]
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lh = int(fnt.size * 1.08); y0 = cy - lh * len(lines) // 2
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
        for i, l in enumerate(lines): sd.text((W // 2 + 3, y0 + i * lh + 4), l, font=fnt, fill=(0, 0, 0, 255), anchor="ma")
        sh = sh.filter(ImageFilter.GaussianBlur(7)); im = Image.alpha_composite(im, sh)
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(2)))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines): d.text((W // 2, y0 + i * lh), l, font=fnt, fill="white", anchor="ma")
    return im


def _typed(text, fnt, cy, type_time, dur, out, shadow=True, width=24):
    """Types the text over `type_time` seconds (in step with the voice), then holds until `dur`."""
    step = type_time / max(len(text), 1)
    steps = [(text[:n] + "|", step) for n in range(1, len(text) + 1)] + [(text + "|", max(dur - type_time, 0.05))]
    lst = []
    for k, (s, d) in enumerate(steps):
        p = f"{out}_{k:03d}.png"; _text_layer(s, fnt, cy, shadow, width).save(p)
        lst.append(f"file '{p.replace(os.sep, '/')}'\nduration {d:.4f}\n")
    lst.append(f"file '{p.replace(os.sep, '/')}'\n"); open(out + ".txt", "w").write("".join(lst))
    return out + ".txt"


def build(project, name, lines, breaks, clips, end, look, voice_ref, tags, progress, check_cancel=lambda: None):
    """clips: one dict per line with 'full' (link). Returns the finished video path."""
    tmp = tempfile.mkdtemp(prefix="clipmaker-")
    try:
        cdir = os.path.join(project, "clips"); os.makedirs(cdir, exist_ok=True)
        files = []
        for i, c in enumerate(clips):
            f = os.path.join(cdir, f"{i:02d}.mp4")
            have = os.path.exists(f) and os.path.exists(f + ".url") and open(f + ".url").read() == c["full"]
            if not have:   # download the full-size clip (skipped if already there)
                open(f, "wb").write(S.get(c["full"], timeout=90).content); open(f + ".url", "w").write(c["full"])
            files.append(f); progress(2 + 6 * i / len(clips), f"downloading clip {i + 1}/{len(clips)}")
        check_cancel()
        progress(8, "making the voice (the slow part)")
        pieces = voice.voice_lines(lines, breaks, voice_ref,
                                   lambda p, m: (check_cancel(), progress(8 + 62 * p, m)))
        serif, sans = _font(tmp, "Lora-normal", 700, 66), _font(tmp, "Inter-normal", 600, 86)
        grade = LOOKS[look]["grade"]; grade = grade + "," if grade else ""
        parts = []
        for i, (line, piece, src) in enumerate(zip(lines, pieces, files)):
            check_cancel()
            dur = len(piece) / SR; spoken = len(voice.trim(piece, keep=0)) / SR
            ov = _typed(line, serif, 1010, spoken * 0.85, dur, os.path.join(tmp, f"t{i}"))
            out = os.path.join(tmp, f"p{i:02d}.mp4")
            vf = (f"[0:v]{grade}scale={W}:1250:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2,"
                  f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2-60:color=0x080808,fps={FPS},setsar=1[v];"
                  f"[1:v]fps={FPS}[t];[v][t]overlay=0:0:shortest=1,format=yuv420p")
            _run([FF, "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", src, "-f", "concat", "-safe", "0",
                  "-i", ov, "-t", f"{dur:.3f}", "-filter_complex", vf, "-an", "-c:v", "libx264", "-crf", "18",
                  "-r", str(FPS), out])
            parts.append(out); progress(70 + 25 * i / len(lines), f"putting clips together {i + 1}/{len(lines)}")
        audio = list(pieces)
        if end.strip():
            a = voice.clean(voice.trim(voice.speak(end, voice_ref)))
            end_dur = len(a) / SR + END_HOLD
            audio.append(np.concatenate([a, np.zeros(int(round(end_dur * SR)) - len(a), np.float32)]))
            bg = os.path.join(tmp, "bg.png"); Image.new("RGB", (W, H), (22, 22, 22)).save(bg)
            ov = _typed(end, sans, 900, len(a) / SR * 0.85, end_dur, os.path.join(tmp, "end"), shadow=False, width=22)
            out = os.path.join(tmp, "p_end.mp4")
            _run([FF, "-loglevel", "error", "-y", "-loop", "1", "-i", bg, "-f", "concat", "-safe", "0", "-i", ov,
                  "-t", f"{end_dur:.3f}", "-filter_complex", f"[1:v]fps={FPS}[t];[0:v][t]overlay=0:0,format=yuv420p",
                  "-c:v", "libx264", "-crf", "18", "-r", str(FPS), out])
            parts.append(out)
        wav = os.path.join(project, name + "-voiceover.wav"); sf.write(wav, np.concatenate(audio), SR)
        lst = os.path.join(tmp, "all.txt")
        open(lst, "w").write("".join(f"file '{p.replace(os.sep, '/')}'\n" for p in parts))
        final = os.path.join(project, name + ".mp4")
        _run([FF, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v",
              "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
              final])
        first = lines[0].rstrip(".…")
        open(os.path.join(project, "caption.txt"), "w", encoding="utf-8").write(
            f"POST CAPTION (copy/paste):\n{first.lower()}… 🤍 {tags}\n\n"
            "Add a soft sound in TikTok at very low volume under the voice.\n")
        progress(100, "done")
        return final
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
