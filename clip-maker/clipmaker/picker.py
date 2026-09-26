"""Finds and picks one clip per script line - no AI chat, just search + free offline image models.

Steps: search the chosen websites -> download small previews -> throw out clips that don't move ->
CLIP (image checker) scores each clip: animated or real, the chosen look, how well it fits each line ->
colour/light numbers for the look -> best clip per line (never the same one twice) ->
OCR (text reader) throws out any clip with words on it (CLIP can read, so it loves meme text).
Every line also keeps a ranked list of runner-ups (saved in project.json)."""
import os, re, json, time, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np, imageio_ffmpeg
from PIL import Image
from .paths import CACHE, device
from .sources import SOURCES, S
from .looks import LOOKS
from .motion import score as motion_score
from . import direct

FF = imageio_ffmpeg.get_ffmpeg_exe()
NOWIN = 0x08000000 if os.name == "nt" else 0   # no console windows popping up on Windows
PER_SEARCH, ALTS, SEARCH_DAYS = 30, 25, 3
SAME_CLIP = 0.93   # image fingerprints this alike = the same clip (Tenor often has one clip under several links)
FEATS = os.path.join(CACHE, "feats"); os.makedirs(FEATS, exist_ok=True)
CARTOON = ["an anime screenshot", "a frame from an animated cartoon", "a hand-drawn illustration"]
REAL = ["a photo of a real person", "a frame from a live-action movie", "a real photograph of people"]
STOP = set("""a an the and or but so if then than that this those these there their they them you your youre i me my
we our us he she it its is are was were be been being am do does did done have has had having to of in on at for
from with without by as into about just not no never ever maybe might may will would could should can cant couldve
wouldve shouldve youll youve dont doesnt isnt wasnt werent wont one some any all more less very really quite little
who what when where why how which get gets got going gonna wanna kind way thing things""".split())


def parse_script(text):
    """One line of text = one clip. Blank lines = pauses: breaks[line number] = how many blank lines follow it
    (1 = short pause, each extra blank line = a longer pause). Voice marks ([sad], *word*, (pause)) are taken out;
    direct.parse() reads them."""
    lines, breaks, _ = direct.parse(text)
    return lines, breaks


def keywords(line):
    w = [x for x in re.findall(r"[a-z]+", line.lower().replace("'", "").replace("’", "")) if x not in STOP and len(x) > 2]
    return " ".join(sorted(w, key=len, reverse=True)[:2])


def _feat_file(url):
    return os.path.join(FEATS, hashlib.md5(url.encode()).hexdigest() + ".npz")


def _cache_file(url):
    return os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + ".mp4")


def _fetch(url):
    f = _cache_file(url)
    if not os.path.exists(f):
        try:
            r = S.get(url, timeout=40)
            if r.status_code != 200 or len(r.content) < 2000: return None
            open(f + ".part", "wb").write(r.content); os.replace(f + ".part", f)
        except Exception:
            return None
    return f


def _frames(f, n=4, size=224):
    raw = subprocess.run([FF, "-loglevel", "error", "-t", "12", "-i", f, "-vf", f"fps=2,scale={size}:{size}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, creationflags=NOWIN).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, size, size, 3)
    return [fr[i] for i in np.linspace(0, len(fr) - 1, n).astype(int)] if len(fr) else []


def _look_numbers(fr):
    hsv = np.stack([np.asarray(Image.fromarray(x).convert("HSV"), np.float32) / 255 for x in fr])
    v, s = hsv[..., 2], hsv[..., 1]
    return dict(bright=float(v.mean()), sat=float(s.mean()), contrast=float(v.std()),
                white=float(((v > 0.88) & (s < 0.12)).mean()))


class _Json:
    """Small on-disk memory so clips already checked are not checked again next time."""
    def __init__(self, name):
        self.path = os.path.join(CACHE, name)
        try: self.d = json.load(open(self.path))
        except Exception: self.d = {}
    def save(self): json.dump(self.d, open(self.path, "w"))


_clip = None
def clip_model():
    global _clip
    if _clip is None:
        import torch
        from transformers import CLIPModel, CLIPProcessor
        dev = device()
        m = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").eval().to(dev)
        _clip = (m, CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32"), dev)
    return _clip


def _feats(o):
    import torch
    return o if torch.is_tensor(o) else o.pooler_output


def img_emb(ims):
    import torch
    m, p, dev = clip_model(); out = []
    with torch.no_grad():
        for i in range(0, len(ims), 64):
            e = _feats(m.get_image_features(**p(images=ims[i:i + 64], return_tensors="pt").to(dev))).float().cpu()
            out.append(e / e.norm(dim=-1, keepdim=True))
    return torch.cat(out)


def txt_emb(t):
    import torch
    m, p, dev = clip_model()
    with torch.no_grad():
        e = _feats(m.get_text_features(**p(text=t, return_tensors="pt", padding=True, truncation=True).to(dev)))
    e = e.float().cpu(); return e / e.norm(dim=-1, keepdim=True)


_ocr = None
def read_text(file):
    """OCR on 3 frames of a clip; returns the words it could read ("" = no text)."""
    global _ocr
    if _ocr is None:
        from rapidocr_onnxruntime import RapidOCR
        _ocr = RapidOCR()
    import tempfile, glob, shutil
    d = tempfile.mkdtemp()
    try:
        subprocess.run([FF, "-loglevel", "error", "-t", "12", "-i", file, "-vf", "fps=2", os.path.join(d, "%03d.png")],
                       capture_output=True, creationflags=NOWIN)
        pngs = sorted(glob.glob(os.path.join(d, "*.png")))
        found = []
        for k in (np.linspace(0, len(pngs) - 1, min(3, len(pngs))).astype(int) if pngs else []):
            try: res, _ = _ocr(pngs[k])
            except Exception: continue
            found += [r[1] for r in res or [] if r[2] > 0.6]
    finally:
        shutil.rmtree(d, ignore_errors=True)
    return " | ".join(found)


def too_much_text(text): return len(re.findall(r"[A-Za-z]", text)) >= 5   # tiny logos/watermarks are ok


def has_words(item, memory):
    """A clip with words on it (memes, captions) is not used."""
    if item.get("checked"): return False          # already checked when the library was built
    if item["full"] not in memory.d:
        memory.d[item["full"]] = read_text(item["file"]); memory.save()
    return too_much_text(memory.d[item["full"]])


def _live_clips(lines, sources, keys, kind, look, progress, themes=True):
    """Searches the websites right now and checks the clips found (remembering everything it works out).
    Returns (clips, fingerprints)."""
    lk = LOOKS[look]
    suffix = {"animated": [" anime", " cartoon"], "real": [""], "both": [" anime", ""]}[kind]
    queries = set()
    for t in (lk["themes"] if themes else []):
        for s in suffix: queries.add(t + s)
    for l in lines:
        k = keywords(l)
        if k:
            for s in suffix: queries.add(k + s)
    jobs = [(src, q) for src in sources for q in sorted(queries)]

    searches = _Json("searches.json")   # search results are remembered for SEARCH_DAYS days
    def run(job):
        src, q = job; key = src + "|" + q; hit = searches.d.get(key)
        if hit and time.time() - hit["t"] < SEARCH_DAYS * 86400: return hit["r"]
        try: r = SOURCES[src][1](q, PER_SEARCH, keys.get(src))
        except Exception: return []
        if r: searches.d[key] = dict(t=time.time(), r=r)
        return r
    progress(2, f"searching {len(sources)} website(s): {len(jobs)} searches")
    cands = {}
    with ThreadPoolExecutor(8) as ex:
        for n, res in enumerate(ex.map(run, jobs)):
            for c in res: cands.setdefault(c["full"], c)
            if n % 10 == 0: progress(2 + 8 * n / len(jobs), f"searching ({n}/{len(jobs)})")
    searches.save()
    items = list(cands.values())
    if not items: return [], np.zeros((0, 512), np.float32)

    progress(10, f"downloading {len(items)} small previews")
    with ThreadPoolExecutor(12) as ex:
        for n, f in enumerate(ex.map(lambda c: _fetch(c["small"]), items)):
            items[n]["file"] = f
            if n % 50 == 0: progress(10 + 20 * n / len(items), f"downloading previews ({n}/{len(items)})")
    items = [c for c in items if c["file"]]

    progress(30, "checking which clips really move")
    motion = _Json("motion.json"); todo = [c for c in items if c["full"] not in motion.d]
    with ThreadPoolExecutor(os.cpu_count() or 4) as ex:
        for n, m in enumerate(ex.map(lambda c: motion_score(c["file"])[1], todo)):
            motion.d[todo[n]["full"]] = float(m)
            if n % 50 == 0: progress(30 + 15 * n / max(len(todo), 1), f"checking movement ({n}/{len(todo)})")
    motion.save()
    items = [c for c in items if motion.d.get(c["full"], 0) >= 1.5]

    # colours + what the image checker sees are worked out once per clip and remembered (feats/ folder),
    # so later videos only look at clips they haven't seen before
    import torch
    todo = [c for c in items if not os.path.exists(_feat_file(c["full"]))]
    progress(45, f"{len(items) - len(todo)} clips already known, looking at {len(todo)} new ones")
    if todo: progress(47, "loading the image checker (first time downloads it)")
    for i in range(0, len(todo), 32):
        batch = []
        for c in todo[i:i + 32]:
            fr = _frames(c["file"])
            if len(fr) >= 2: batch.append((c, fr))
        if batch:
            e = img_emb([Image.fromarray(x) for _, fr in batch for x in fr]).view(len(batch), -1, 512).mean(1)
            for (c, fr), v in zip(batch, e):
                np.savez(_feat_file(c["full"]), emb=v.numpy().astype(np.float16), **_look_numbers(fr))
        progress(47 + 36 * i / max(len(todo), 1), f"image checker: {i}/{len(todo)} new clips")
    good, E = [], []
    for c in items:
        f = _feat_file(c["full"])
        if not os.path.exists(f): continue
        z = np.load(f); c.update({k: float(z[k]) for k in ("bright", "sat", "contrast", "white")})
        E.append(z["emb"].astype(np.float32)); good.append(c)
    E = np.stack(E) if E else np.zeros((0, 512), np.float32)
    return good, E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-6)


def find_clips(lines, sources, keys, kind, look, progress, live=False):
    """kind: 'animated' | 'real' | 'both'. Returns one ranked candidate list per line (best first).
    Uses the ready-made clip library when there is one (seconds); live=True (or no library) also searches
    the websites right now (minutes, but can find newer clips)."""
    import torch
    from . import library
    lk = LOOKS[look]
    lib = library.load() if "tenor" in sources else None
    items, Es = [], []
    if lib:
        _, clips, LE = lib
        progress(5, f"clip library: {len(clips)} clips")
        items += [dict(c, source="tenor", file=None) for c in clips]; Es.append(LE)
    others = [s for s in sources if s != "tenor"]
    if live or not lib or others:
        srcs = sources if (live or not lib) else others
        li, le = _live_clips(lines, srcs, keys, kind, look,
                             (lambda p, m: progress(5 + 0.75 * p, m)), themes=not lib)
        known = {c["full"] for c in items}
        keep = [n for n, c in enumerate(li) if c["full"] not in known]
        items += [li[n] for n in keep]; Es.append(le[keep])
    if not items: raise RuntimeError("No clips found - check your internet and the website keys in Settings.")
    E = torch.from_numpy(np.concatenate(Es).astype(np.float32))

    def prob(pos, neg):
        T = txt_emb(pos + neg); p = (100 * E @ T.T).softmax(-1)
        return p[:, :len(pos)].sum(-1).numpy()
    cartoon = prob(CARTOON, REAL)
    mood = prob(lk["good"], lk["bad"]) if lk["good"] else np.zeros(len(items))
    keep = []
    for k, c in enumerate(items):
        if kind == "animated" and cartoon[k] < 0.75: continue
        if kind == "real" and cartoon[k] > 0.3: continue
        if c.get("white", 0) > 0.35: continue
        tone = 0.0
        if lk["target"]:
            tb, ts = lk["target"]
            tone = 1 - abs(c["bright"] - tb) * 2 - abs(c["sat"] - ts) * 1.5 - c["white"] * 3 + min(c["contrast"], 0.25)
        c["look"] = 0.6 * float(mood[k]) + 0.4 * tone
        keep.append(k)
    if len(keep) < len(lines): raise RuntimeError(f"Only {len(keep)} usable clips found - try more websites or 'both'.")
    items = [items[k] for k in keep]; E = E[keep]

    progress(85, "matching clips to your lines")
    rel = (100 * txt_emb(lines) @ E.T).numpy()
    rel = (rel - rel.mean(1, keepdims=True)) / (rel.std(1, keepdims=True) + 1e-6)
    look_s = np.array([c["look"] for c in items]); look_s = (look_s - look_s.mean()) / (look_s.std() + 1e-6)
    total = rel + (0.9 * look_s if lk["target"] else 0)

    ocr_mem = _Json("ocr.json")
    En = E.numpy()
    look_alike = lambda j: np.where(En @ En[j] > SAME_CLIP)[0]   # the same clip uploaded again under another link
    pick, banned = [None] * len(lines), set()
    grid = total.copy()
    while None in pick:  # best line/clip pair first, so strong matches aren't stolen by weak ones
        i, j = np.unravel_index(np.argmax(grid), grid.shape)
        if has_words(items[j], ocr_mem): banned.add(j); grid[:, j] = -np.inf; continue
        grid[:, look_alike(j)] = -np.inf   # never the same (or a look-alike) clip twice in one video
        pick[i] = j; grid[i, :] = -np.inf
        progress(85 + 12 * sum(p is not None for p in pick) / len(lines), "checking picked clips for text")
    out, group, seen = [], {}, []
    for i, j in enumerate(pick):
        ranked = [j] + [k for k in np.argsort(-total[i]) if k != j and k not in banned][:ALTS]
        for k in ranked:   # look-alike clips share a group number, so the video builder uses only one of them
            if k in group: continue
            g = next((group[s] for s in seen if En[s] @ En[k] > SAME_CLIP), len(seen))
            group[k] = g; seen.append(k)
        out.append([dict(full=items[k]["full"], small=items[k]["small"], file=items[k].get("file"),
                         desc=items[k]["desc"], source=items[k]["source"], fit=round(float(rel[i, k]), 2),
                         group=int(group[k]), checked=bool(items[k].get("checked")))
                    for k in ranked])
    return out

