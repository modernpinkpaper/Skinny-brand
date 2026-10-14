"""Renders the animation frames (4 browser workers in parallel), then encodes the video with the audio.

  python render.py <work folder with timeline.json + audio.wav> <out.mp4> [--seconds N] [--start S]
Needs Chromium (playwright). Set CHROMIUM_PATH if it isn't found automatically."""
import os, sys, json, subprocess, multiprocessing as mp

HERE = os.path.dirname(os.path.abspath(__file__))

def worker(args):
    work, a, b, wid = args
    from playwright.sync_api import sync_playwright
    tl = json.load(open(os.path.join(work, "timeline.json")))
    with sync_playwright() as p:
        kw = dict(args=["--no-sandbox"])
        if os.environ.get("CHROMIUM_PATH"): kw["executable_path"] = os.environ["CHROMIUM_PATH"]
        br = p.chromium.launch(**kw); pg = br.new_page(viewport=dict(width=1080, height=1920))
        pg.on("pageerror", lambda e: print("PAGE ERROR", e, flush=True))
        pg.goto("file://" + os.path.join(HERE, "anim.html")); pg.evaluate("tl=>window.init(tl)", tl)
        for f in range(a, b):
            pg.evaluate("f=>window.frame(f)", f)
            pg.screenshot(path=os.path.join(work, "frames", f"{f:05d}.jpg"), type="jpeg", quality=92)
            if (f - a) % 100 == 0: print(f"worker {wid}: frame {f}/{b}", flush=True)
        br.close()

def main():
    work, out = sys.argv[1], sys.argv[2]
    tl = json.load(open(os.path.join(work, "timeline.json"))); fps = tl["fps"]
    start = int(float(sys.argv[sys.argv.index("--start") + 1]) * fps) if "--start" in sys.argv else 0
    total = int(tl["duration"] * fps)
    end = min(total, start + int(float(sys.argv[sys.argv.index("--seconds") + 1]) * fps)) if "--seconds" in sys.argv else total
    os.makedirs(os.path.join(work, "frames"), exist_ok=True)
    n = 4; step = (end - start + n - 1) // n
    jobs = [(work, start + i * step, min(end, start + (i + 1) * step), i) for i in range(n) if start + i * step < end]
    with mp.Pool(n) as pool: pool.map(worker, jobs)
    ss = start / fps
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", str(start), "-i", os.path.join(work, "frames", "%05d.jpg"),
                    "-ss", str(ss), "-i", os.path.join(work, "audio.wav"), "-t", str((end - start) / fps),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", out], check=True)
    print("saved", out)

if __name__ == "__main__":
    main()
