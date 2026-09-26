#!/usr/bin/env python3
"""Script in, finished video out - no AI chat needed.

  python clip-videos/auto_video.py my-script.txt --name absent-parent --clone clip-videos/voices/guy-ref.wav

What it does, start to finish:
 1. Reads the script: one line of text = one clip. A blank line = a short pause in the voice.
 2. Searches Tenor for animated clips: words from each line + "anime"/"cartoon", plus general
    searches for the chosen mood (--style).
 3. Downloads small previews and scores every clip with CLIP (a free image model that runs offline):
      - cartoon or real? (real photos / real people are thrown out)
      - does it fit the line's words?
      - does it have the look you want? (moody = darker, softer colours, no white backgrounds)
      - does it really move? (motion_check.py) and does it have words baked in? (thrown out / marked down)
 4. Gives every line its best clip (never the same clip twice) and saves a preview sheet (preview.png).
 5. Builds the video with make_video.py (voice + typed text + colour grade) and writes caption.txt.

To swap a clip you don't like: put another Tenor link on that line of <folder>/clips.txt, delete
<folder>/clips/NN.mp4 and run make_video.py for that folder (see the last line this prints).
"""
import os, re, sys, json, argparse, subprocess, urllib.parse, requests, numpy as np, imageio_ffmpeg
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from motion_check import score as motion_score

STYLES = {  # extra searches + what CLIP should see, per look
    "moody": dict(
        searches=["sad anime rain", "anime night window", "anime alone room", "lonely anime", "anime sunset sad",
                  "anime train window", "anime walking alone night", "ghibli rain", "anime city night lights",
                  "sad anime girl", "sad anime boy", "anime hug", "anime crying", "anime looking at sky",
                  "anime friends", "anime healing", "anime memories", "anime dusk", "anime quiet", "anime tears"],
        good=["a moody, dim anime scene with muted colours", "a quiet melancholic anime frame at night or dusk",
              "a soft, desaturated, cinematic animated scene"],
        bad=["a bright, colourful, cheerful cartoon", "a cartoon sticker on a white background",
             "a neon, saturated, loud animation"],
        grade="moody"),
}
CARTOON = ["an anime screenshot", "a frame from an animated cartoon", "a hand-drawn illustration"]
REAL = ["a photo of a real person", "a frame from a live-action movie", "a real photograph of people"]
TEXTY = ["an image with big words and captions written on it", "a meme with text"]
PLAIN = ["an image with no text"]
TEXT_WORDS = re.compile(r"\b(says|saying|words?|written|text|caption|logo|reads|sign that)\b")
PER_SEARCH = 30   # top results kept from each search
STOP = set("""a an the and or but so if then than that this those these there their they them you your you're youre i
me my we our us he she it its is are was were be been being am do does did done have has had having to of in on at
for from with without by as into about just not no never ever maybe might may will would could should can cant
couldve wouldve shouldve youll youve dont doesnt isnt wasnt werent won't wont one some any all more less very
really quite little who what when where why how which get gets got going gonna wanna kind way thing things""".split())

ap = argparse.ArgumentParser()
ap.add_argument("script", help="text file: one line per clip, blank line = pause")
ap.add_argument("--name", help="folder name under clip-videos/ (default: script file name)")
ap.add_argument("--style", default="moody", choices=STYLES)
ap.add_argument("--clone", help="voice to copy (wav). Without it the free Kokoro voice is used")
ap.add_argument("--voice", default="af_heart", help="Kokoro voice when not cloning")
ap.add_argument("--end", default="send this to someone who needs to hear it", help="end-screen line")
ap.add_argument("--tags", default="#healing #innerchild #selflove #emotionalhealing #relatable #anime #fyp")
ap.add_argument("--pick-only", action="store_true", help="just pick clips + preview, don't build the video")
args = ap.parse_args()
style = STYLES[args.style]
name = args.name or os.path.splitext(os.path.basename(args.script))[0]
OUT = os.path.join(HERE, name); os.makedirs(os.path.join(OUT, "clips"), exist_ok=True)
CACHE = os.path.join(HERE, ".tenor-cache"); os.makedirs(CACHE, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"
log = lambda *a: print(*a, flush=True)

# ---- 1. script ----
LINES, BREAKS = [], []
for raw in open(args.script, encoding="utf-8"):
    t = raw.strip().lstrip(">").strip()
    if t: LINES.append(t)
    elif LINES and (not BREAKS or BREAKS[-1] != len(LINES) - 1): BREAKS.append(len(LINES) - 1)
log(f"{len(LINES)} lines, {len(BREAKS)} pauses")

# ---- 2. search ----
def keywords(line):
    w = [x for x in re.findall(r"[a-z]+", line.lower().replace("'", "")) if x not in STOP and len(x) > 2]
    return " ".join(sorted(w, key=len, reverse=True)[:2])

def search(q):
    u = "https://tenor.com/search/" + urllib.parse.quote(q.replace(" ", "-")) + "-gifs"
    try: s = S.get(u, timeout=30).text.replace("\\u002F", "/")
    except requests.RequestException: return []
    parts = s.split('"content_description":"'); out = []
    for prev, cur in zip(parts, parts[1:]):
        urls = re.findall(r'"mp4":\{"url":"(https://media\.tenor\.com/[^"]+\.mp4)"', prev[-6000:])
        if urls: out.append((urls[-1], cur.split('"', 1)[0]))
    return out[:PER_SEARCH]

queries = set(style["searches"])
for l in LINES:
    k = keywords(l)
    if k: queries |= {k + " anime", k + " cartoon"}
log(f"searching Tenor: {len(queries)} searches")
with ThreadPoolExecutor(8) as ex: results = list(ex.map(search, sorted(queries)))
cands = {}
for res in results:
    for url, desc in res: cands.setdefault(url, desc)
log(f"{len(cands)} different clips found")

# ---- 3. download previews + score ----
def small(url): return url.replace("AAAPo/", "AAAP1/")  # Tenor's 320px version, fast to check
def fetch(url):
    f = os.path.join(CACHE, re.sub(r"\W", "_", url.split("media.tenor.com/")[1])[:120])
    if not os.path.exists(f):
        try:
            r = S.get(small(url), timeout=30)
            if r.status_code != 200 or len(r.content) < 2000: return None
            open(f, "wb").write(r.content)
        except requests.RequestException: return None
    return f

def frames(f, n=4):
    raw = subprocess.run([FF, "-loglevel", "error", "-i", f, "-vf", "fps=4,scale=224:224", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 224, 224, 3)
    if len(fr) == 0: return []
    return [fr[i] for i in np.linspace(0, len(fr) - 1, n).astype(int)]

def look(fr):
    """Colour/light numbers: brightness, colour strength, contrast, share of white background."""
    hsv = np.stack([np.asarray(Image.fromarray(x).convert("HSV"), np.float32) / 255 for x in fr])
    v, s = hsv[..., 2], hsv[..., 1]
    return dict(bright=float(v.mean()), sat=float(s.mean()), contrast=float(v.std()),
                white=float(((v > 0.88) & (s < 0.12)).mean()))

log("downloading previews")
urls = list(cands)
with ThreadPoolExecutor(12) as ex: files = list(ex.map(fetch, urls))
items = []
for url, f in zip(urls, files):
    if not f: continue
    fr = frames(f)
    if len(fr) < 2: continue
    items.append(dict(url=url, desc=cands[url], file=f, frames=fr, **look(fr)))
log(f"{len(items)} previews ok, checking motion")
MC = os.path.join(CACHE, "motion.json")
mcache = json.load(open(MC)) if os.path.exists(MC) else {}
todo = [it for it in items if it["url"] not in mcache]
with ThreadPoolExecutor(4) as ex: moves = list(ex.map(lambda it: motion_score(it["file"])[1], todo))
for it, m in zip(todo, moves): mcache[it["url"]] = float(m)
json.dump(mcache, open(MC, "w"))
for it in items: it["motion"] = mcache[it["url"]]
items = [it for it in items if it["motion"] >= 1.5]
log(f"{len(items)} clips really move; scoring with CLIP")

import torch
from transformers import CLIPModel, CLIPProcessor
torch.set_num_threads(os.cpu_count())
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval()
proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
feats = lambda o: o if torch.is_tensor(o) else o.pooler_output   # newer transformers wrap the result
@torch.no_grad()
def img_emb(ims):
    out = []
    for i in range(0, len(ims), 64):
        e = feats(model.get_image_features(**proc(images=ims[i:i + 64], return_tensors="pt")))
        out.append(e / e.norm(dim=-1, keepdim=True))
    return torch.cat(out)
@torch.no_grad()
def txt_emb(t):
    e = feats(model.get_text_features(**proc(text=t, return_tensors="pt", padding=True, truncation=True)))
    return e / e.norm(dim=-1, keepdim=True)

E = img_emb([Image.fromarray(x) for it in items for x in it["frames"]])
E = E.view(len(items), -1, E.shape[-1]).mean(1); E = E / E.norm(dim=-1, keepdim=True)
def prob(pos, neg):  # CLIP zero-shot: chance the clip looks like `pos` rather than `neg`
    T = txt_emb(pos + neg); p = (100 * E @ T.T).softmax(-1)
    return p[:, :len(pos)].sum(-1).numpy()
cartoon, moody, texty = prob(CARTOON, REAL), prob(style["good"], style["bad"]), prob(TEXTY, PLAIN)

keep = []
for k, it in enumerate(items):
    it.update(cartoon=float(cartoon[k]), mood_clip=float(moody[k]), texty=float(texty[k]))
    # light/colour score for "moody": darker-than-average, softer colours, no white background
    if args.style == "moody":
        tone = 1 - abs(it["bright"] - 0.38) * 2 - abs(it["sat"] - 0.28) * 1.5 - it["white"] * 3 + min(it["contrast"], 0.25)
    else:
        tone = 0
    it["look"] = 0.6 * it["mood_clip"] + 0.4 * tone
    it["text_pen"] = 0.5 * it["texty"] + (0.3 if TEXT_WORDS.search(it["desc"].lower()) else 0)
    if it["cartoon"] >= 0.75 and it["white"] < 0.35: keep.append(k)
log(f"{len(keep)} clips are animated and not on a white background")
items = [items[k] for k in keep]; E = E[keep]

# ---- 4. pick one clip per line ----
rel = (100 * txt_emb(LINES) @ E.T).numpy()                     # how well each clip fits each line
rel = (rel - rel.mean(1, keepdims=True)) / (rel.std(1, keepdims=True) + 1e-6)
look_s = np.array([it["look"] for it in items]); look_s = (look_s - look_s.mean()) / (look_s.std() + 1e-6)
pen = np.array([it["text_pen"] for it in items])
total = rel + 0.9 * look_s - 2.0 * pen
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
OC = os.path.join(CACHE, "ocr.json")
ocache = json.load(open(OC)) if os.path.exists(OC) else {}
def has_words(it):
    """Reads 3 frames with OCR. Clips with meme text / captions are skipped: CLIP can read,
    so it would otherwise pick a clip just because it says the line's words."""
    if it["url"] not in ocache:
        raw = subprocess.run([FF, "-loglevel", "error", "-i", it["file"], "-vf", "fps=2", "-f", "image2pipe",
                              "-vcodec", "png", "-"], capture_output=True).stdout
        pngs = [b"\x89PNG" + x for x in raw.split(b"\x89PNG")[1:]]
        found = []
        for png in [pngs[k] for k in np.linspace(0, len(pngs) - 1, min(3, len(pngs))).astype(int)] if pngs else []:
            res, _ = ocr(png)
            found += [r[1] for r in res or [] if r[2] > 0.6]
        ocache[it["url"]] = " | ".join(found)
        json.dump(ocache, open(OC, "w"))
    return len(re.findall(r"[A-Za-z]", ocache[it["url"]])) >= 5   # tiny logos/watermarks pass

pick, used = [None] * len(LINES), set()
while None in pick:  # best line/clip pair first, so strong matches aren't stolen by weak ones
    best = max(((total[i, j], i, j) for i in range(len(LINES)) if pick[i] is None
                for j in range(len(items)) if j not in used))
    _, i, j = best; used.add(j)
    if has_words(items[j]): continue   # has words on it: skip this clip, try the next best
    pick[i] = j
log(f"checked {len(used)} clips for words, {len(used) - len(LINES)} skipped")

report = []
for i, j in enumerate(pick):
    it = items[j]
    report.append(dict(line=LINES[i], url=it["url"], desc=it["desc"], fit=round(float(rel[i, j]), 2),
                       look=round(float(look_s[j]), 2), cartoon=round(it["cartoon"], 2),
                       bright=round(it["bright"], 2), colour=round(it["sat"], 2)))
json.dump(report, open(os.path.join(OUT, "picks.json"), "w"), indent=1)

# preview sheet: line text + 3 frames of its clip
rows = []
for i, j in enumerate(pick):
    strip = Image.new("RGB", (3 * 160 + 360, 120), (20, 20, 20)); d = ImageDraw.Draw(strip)
    for k, x in enumerate(items[j]["frames"][:3]): strip.paste(Image.fromarray(x).resize((160, 120)), (360 + k * 160, 0))
    d.text((8, 8), f"{i:02d}", fill=(255, 120, 120))
    for n, part in enumerate(re.findall(r".{1,44}(?:\s|$)", LINES[i])[:5]): d.text((36, 8 + n * 16), part.strip(), fill="white")
    rows.append(strip)
sheet = Image.new("RGB", (rows[0].width, 122 * len(rows)), "black")
for n, r in enumerate(rows): sheet.paste(r, (0, n * 122))
sheet.save(os.path.join(OUT, "preview.png"))

# ---- 5. write the folder make_video.py reads, get full-size clips, build ----
with open(os.path.join(OUT, "script.py"), "w") as f:
    f.write("# made by auto_video.py (on-screen line + voiceover, search words)\nLINES = [\n")
    for l in LINES: f.write(f" ({l!r}, {keywords(l)!r}),\n")
    f.write(f"]\nEND = {args.end!r}\nBREAKS = {BREAKS!r}\n")
with open(os.path.join(OUT, "clips.txt"), "w") as f:
    f.write(f"# picked automatically by auto_video.py (style: {args.style}) - swap any link you don't like\n")
    for j in pick: f.write(items[j]["url"] + "\n")
for n, j in enumerate(pick):
    p = os.path.join(OUT, "clips", f"{n:02d}.mp4")
    open(p, "wb").write(S.get(items[j]["url"], timeout=60).content)
first = LINES[0].rstrip(".…")
open(os.path.join(OUT, "caption.txt"), "w").write(
    f"POST CAPTION (copy/paste):\n{first.lower()}… 🤍 {args.tags}\n\n"
    f"VOICEOVER: already in the video. Add a soft sound in TikTok at very low volume under it.\n"
    f"CLIPS: picked automatically (animated only, {args.style} look) - see preview.png and picks.json.\n")
log(f"picked clips -> {OUT}/preview.png")

cmd = [sys.executable, os.path.join(HERE, "make_video.py"), OUT, "--flow", "--out", name + ".mp4"]
if style.get("grade"): cmd += ["--grade", style["grade"]]
cmd += ["--clone", args.clone] if args.clone else ["--voice", args.voice]
if args.pick_only:
    log("build it with:\n  " + " ".join(cmd))
else:
    log("building video")
    subprocess.run(cmd, check=True)
