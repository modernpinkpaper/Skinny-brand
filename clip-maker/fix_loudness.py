"""Brings older finished videos up to normal TikTok loudness, the same way new videos are made
(see LOUD in clipmaker/render.py). Used by the "Fix loudness" workflow.

  python fix_loudness.py <release tag>

For every video on that release page it measures the voice. Anything quieter than -18 LUFS gets the voice evened out and normalized to about -14 LUFS, and
replaces the video on the release page under the same name. The picture is copied, not re-encoded.
Videos that are already loud are left alone, so running it twice is harmless."""
import json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
# Read LOUD from render.py's text (importing it would pull in the whole video toolchain).
_src = open(os.path.join(HERE, "clipmaker", "render.py"), encoding="utf-8").read()
LOUD = "".join(re.findall(r'"([^"]*)"', re.search(r"^LOUD = \((.*?)\)\s*$", _src, re.S | re.M).group(1)))
QUIET = -18.0   # anything below this is an old, quiet video


def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", "loudnorm=print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(json.loads(err[err.rindex("{"):err.rindex("}") + 1])["input_i"])


def main(tag):
    assets = json.loads(gh("release", "view", tag, "--json", "assets"))["assets"]
    videos = sorted(a["name"] for a in assets if a["name"].endswith(".mp4"))
    print(f"{len(videos)} videos on {tag}", flush=True)
    tmp = tempfile.mkdtemp()
    fixed = skipped = 0
    for name in videos:
        src, out_dir = os.path.join(tmp, name), os.path.join(tmp, "out")
        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, name)
        gh("release", "download", tag, "-p", name, "-D", tmp, "--clobber")
        before = loudness(src)
        if before > QUIET:
            print(f"already loud ({before:.1f} LUFS): {name}", flush=True)
            skipped += 1
        else:
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-map", "0:v", "-map", "0:a",
                            "-c:v", "copy", "-af", LOUD, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                            out], check=True)
            after = loudness(out)
            gh("release", "upload", tag, out, "--clobber")
            print(f"fixed {before:.1f} -> {after:.1f} LUFS: {name}", flush=True)
            fixed += 1
        for p in (src, out):
            if os.path.exists(p):
                os.remove(p)
    print(f"Done: {fixed} fixed, {skipped} were already loud.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "videos-life-changing-sentences")
