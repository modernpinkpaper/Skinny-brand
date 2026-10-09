#!/usr/bin/env python3
"""Get a transcript for every video on a public TikTok account.
Usage: python3 tools/tiktok_transcripts.py connectingherdots [out_dir]
Uses TikTok's own captions when a video has them, otherwise listens to the audio with faster-whisper."""
import os, sys, json, glob, subprocess, tempfile

user = sys.argv[1].lstrip("@")
out = sys.argv[2] if len(sys.argv) > 2 else "research/transcripts-" + user
os.makedirs(out, exist_ok=True)
YT = [sys.executable, "-m", "yt_dlp", "--impersonate", "chrome"]

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

r = run(YT + ["--flat-playlist", "--print", "%(id)s\t%(webpage_url)s", f"https://www.tiktok.com/@{user}"])
print(r.stderr[-1500:], file=sys.stderr)
videos = [l.split("\t") for l in r.stdout.splitlines() if "\t" in l]
print(f"found {len(videos)} videos", flush=True)
if not videos:
    sys.exit("could not list the account's videos")

_wm = None
def whisper(path):
    global _wm
    if _wm is None:
        from faster_whisper import WhisperModel
        _wm = WhisperModel("base.en", device="cpu", compute_type="int8")
    segs, _ = _wm.transcribe(path, vad_filter=True)
    return " ".join(s.text.strip() for s in segs).strip()

results = []
for i, (vid, url) in enumerate(videos, 1):
    dest = os.path.join(out, vid + ".json")
    if os.path.exists(dest):
        results.append(json.load(open(dest))); continue
    with tempfile.TemporaryDirectory() as td:
        run(YT + ["-f", "worst[ext=mp4]/worst", "-o", td + "/v.%(ext)s", "--write-info-json", url])
        media = [p for p in glob.glob(td + "/v.*") if not p.endswith(".json")]
        info = {}
        if glob.glob(td + "/v.info.json"):
            info = json.load(open(td + "/v.info.json"))
        text, how = "", ""
        if media:
            text, how = whisper(media[0]), "whisper"
        rec = {"id": vid, "url": url, "description": info.get("description", ""),
               "duration": info.get("duration"), "views": info.get("view_count"),
               "likes": info.get("like_count"), "transcript": text, "source": how}
    json.dump(rec, open(dest, "w"), indent=1)
    results.append(rec)
    print(i, len(videos), vid, len(rec["transcript"].split()), "words", flush=True)

with open(os.path.join(out, "ALL.md"), "w") as f:
    f.write(f"# Transcripts: @{user}\n\n")
    for r_ in results:
        if r_["transcript"]:
            f.write(f"## {r_['id']} ({r_.get('duration')}s, {r_.get('views')} views)\n{r_['url']}\n\n{r_['transcript']}\n\n")
print("done", sum(1 for r_ in results if r_["transcript"]), "with text")
