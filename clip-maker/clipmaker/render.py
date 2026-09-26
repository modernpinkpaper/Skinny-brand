"""Puts it together: each clip on a dark 9:16 frame, colour-graded, the line typed on screen while the
voice says it, then an end screen. Saves <project>/<name>.mp4, the voiceover .wav and caption.txt."""
import os, re, subprocess, tempfile, textwrap, shutil
import numpy as np, soundfile as sf, imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from .paths import ASSETS
from .sources import S
from .looks import LOOKS
from . import voice, captions

FF = imageio_ffmpeg.get_ffmpeg_exe()
W, H, FPS, SR = 1080, 1920, 30, voice.SR
END_HOLD = 2.5
NOWIN = 0x08000000 if os.name == "nt" else 0   # no black console windows popping up on Windows


def _run(cmd): subprocess.run(cmd, check=True, creationflags=NOWIN)


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


SLOWEST, GENTLE, MAX_CLIPS = 0.6, 0.85, 3   # never slower than 60% speed; when joining clips, play them at 85%


def clip_seconds(f):
    """Real length of a clip (decodes it, because GIF-style mp4s often report no length)."""
    r = subprocess.run([FF, "-i", f, "-map", "0:v:0", "-f", "null", "-"], capture_output=True, text=True,
                       creationflags=NOWIN).stderr
    t = re.findall(r"time=(\d+):(\d+):([\d.]+)", r)
    return int(t[-1][0]) * 3600 + int(t[-1][1]) * 60 + float(t[-1][2]) if t else 0.0


def _download(c, path):
    if os.path.exists(path) and os.path.exists(path + ".url") and open(path + ".url").read() == c["full"]:
        return True
    try:
        r = S.get(c["full"], timeout=90)
        if r.status_code == 200 and len(r.content) > 5000:
            open(path, "wb").write(r.content); open(path + ".url", "w").write(c["full"]); return True
    except Exception:
        pass
    return False


def _fill(options, dur, used, stem):
    """Which clips fill a line of `dur` seconds without looping: (file, speed, seconds, loop) per clip.
    A clip long enough is just cut; a bit too short is slowed down to fit (not below SLOWEST);
    much too short is played at GENTLE speed and the line's next best clip follows (up to MAX_CLIPS)."""
    plan, left, n = [], dur, 0
    for c in options:   # best first; a clip that's gone from the website is skipped
        if c["full"] in used: continue
        f = f"{stem}_{n}.mp4"
        if not _download(c, f): continue
        L = clip_seconds(f)
        if L < 0.3: continue
        used.add(c["full"]); n += 1
        if L >= left: plan.append((f, 1.0, left, False)); return plan
        if L / SLOWEST >= left: plan.append((f, L / left, left, False)); return plan
        if n == MAX_CLIPS: plan.append((f, SLOWEST, left, True)); return plan   # last resort: loop slowly
        take = L / GENTLE; plan.append((f, GENTLE, take, False)); left -= take
    if plan:   # ran out of options: stretch the last clip over what's left
        f, spd, take, _ = plan[-1]; plan[-1] = (f, spd, take + left, True); return plan
    raise RuntimeError("Couldn't download any clip for one of the lines - check your internet.")


def make_voice(lines, breaks, end, voice_ref, speed=1.0, progress=lambda p, m: None):
    """All the audio: one piece per line (+ word timings) and the end-screen line.
    Can run while the clips are being found."""
    pieces, times = voice.voice_lines(lines, breaks, voice_ref, speed, progress)
    end_audio = voice.clean(voice.trim(voice.speak(end, voice_ref, speed))) if end.strip() else None
    return pieces, times, end_audio


def build(project, name, lines, breaks, clips, end, look, voice_ref, tags, progress, check_cancel=lambda: None,
          audio_parts=None, speed=1.0):
    """clips: per line, a list of clip dicts best-first (or one dict). audio_parts: result of make_voice().
    Returns the finished video path."""
    tmp = tempfile.mkdtemp(prefix="clipmaker-")
    try:
        check_cancel()
        if audio_parts is None:
            progress(2, "making the voice (the slow part)")
            audio_parts = make_voice(lines, breaks, end, voice_ref, speed,
                                     lambda p, m: (check_cancel(), progress(2 + 60 * p, m)))
        pieces, times, end_audio = audio_parts
        sans = captions.font(90)
        grade = LOOKS[look]["grade"]; grade = grade + "," if grade else ""
        cdir = os.path.join(project, "clips"); os.makedirs(cdir, exist_ok=True)
        used, parts = set(), []
        for i, (line, piece, wt) in enumerate(zip(lines, pieces, times)):
            check_cancel()
            dur = len(piece) / SR
            options = clips[i] if isinstance(clips[i], list) else [clips[i]]
            plan = _fill(options, dur, used, os.path.join(cdir, f"{i:02d}"))   # clips that fill the line, no looping
            print(f"line {i + 1} ({dur:.1f}s): " + " + ".join(
                f"clip {k + 1} {t:.1f}s at {sp:.0%} speed" + (" (looped)" if lp else "")
                for k, (_, sp, t, lp) in enumerate(plan)), flush=True)
            base = os.path.join(tmp, f"b{i:02d}.mp4"); subs = []
            for k, (f, spd, take, loop) in enumerate(plan):
                sub = os.path.join(tmp, f"b{i:02d}_{k}.mp4"); subs.append(sub)
                vf = (f"{grade}setpts=PTS/{spd:.4f},scale={W}:1250:force_original_aspect_ratio=decrease,"
                      f"scale=trunc(iw/2)*2:trunc(ih/2)*2,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2-60:color=0x080808,"
                      f"fps={FPS},setsar=1,format=yuv420p")
                _run([FF, "-loglevel", "error", "-y"] + (["-stream_loop", "-1"] if loop else []) + ["-i", f,
                      "-t", f"{take:.3f}", "-vf", vf, "-an", "-c:v", "libx264", "-crf", "18", "-r", str(FPS), sub])
            lst = os.path.join(tmp, f"b{i:02d}.txt")
            open(lst, "w").write("".join(f"file '{x.replace(os.sep, '/')}'\n" for x in subs))
            _run([FF, "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base])
            ov = captions.line_overlay(line, wt, dur, os.path.join(tmp, f"t{i}"))   # words pop in as they're said
            out = os.path.join(tmp, f"p{i:02d}.mp4")
            _run([FF, "-loglevel", "error", "-y", "-i", base, "-f", "concat", "-safe", "0", "-i", ov,
                  "-t", f"{dur:.3f}", "-filter_complex", f"[1:v]fps={FPS}[t];[0:v][t]overlay=0:0,format=yuv420p",
                  "-an", "-c:v", "libx264", "-crf", "18", "-r", str(FPS), out])
            parts.append(out); progress(62 + 33 * i / len(lines), f"putting clips together {i + 1}/{len(lines)}")
        audio = list(pieces)
        if end_audio is not None:
            a = np.concatenate([np.zeros(int(0.5 * SR), np.float32), end_audio])   # a breath before the end line
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
