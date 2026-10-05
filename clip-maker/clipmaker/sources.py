"""Clip websites. Each search returns dicts: full (link to the clip), small (a small preview to check),
desc (words describing it), source. Tenor needs nothing; the others need a free key from their website."""
import os, re, json, shutil, subprocess, urllib.parse, requests

S = requests.Session(); S.headers["User-Agent"] = "Mozilla/5.0"


def tenor(q, n, key=None):
    u = "https://tenor.com/search/" + urllib.parse.quote(q.replace(" ", "-")) + "-gifs"
    s = S.get(u, timeout=30).text.replace("\\u002F", "/")
    parts = s.split('"content_description":"'); out, seen = [], set()
    for prev, cur in zip(parts, parts[1:]):
        urls = re.findall(r'"mp4":\{"url":"(https://media\.tenor\.com/[^"]+\.mp4)"', prev[-6000:])
        if not urls or urls[-1] in seen: continue
        seen.add(urls[-1])
        out.append(dict(full=urls[-1], small=urls[-1].replace("AAAPo/", "AAAP1/"), desc=cur.split('"', 1)[0],
                        source="tenor"))
    return out[:n]


def giphy(q, n, key):
    r = S.get("https://api.giphy.com/v1/gifs/search",
              params=dict(api_key=key, q=q, limit=n, rating="pg-13"), timeout=30).json()
    out = []
    for g in r.get("data", []):
        im = g.get("images", {})
        full = im.get("original", {}).get("mp4"); small = im.get("fixed_width", {}).get("mp4") or full
        if full: out.append(dict(full=full, small=small, desc=g.get("alt_text") or g.get("title", ""), source="giphy"))
    return out


def pexels(q, n, key):
    r = S.get("https://api.pexels.com/videos/search", params=dict(query=q, per_page=n),
              headers={"Authorization": key}, timeout=30).json()
    out = []
    for v in r.get("videos", []):
        files = sorted([f for f in v.get("video_files", []) if f.get("width") and f.get("file_type") == "video/mp4"],
                       key=lambda f: f["width"])
        if not files: continue
        full = min(files, key=lambda f: abs(f["width"] - 1080))["link"]
        small = next((f for f in files if f["width"] >= 320), files[0])["link"]
        slug = v.get("url", "").rstrip("/").split("/")[-1]
        out.append(dict(full=full, small=small, desc=re.sub(r"[-\d]+", " ", slug).strip(), source="pexels"))
    return out


def pixabay(q, n, key):
    r = S.get("https://pixabay.com/api/videos/", params=dict(key=key, q=q, per_page=max(3, min(n, 200))),
              timeout=30).json()
    out = []
    for h in r.get("hits", []):
        v = h.get("videos", {})
        full = (v.get("medium") or v.get("large") or {}).get("url")
        small = (v.get("tiny") or v.get("small") or {}).get("url") or full
        if full: out.append(dict(full=full, small=small, desc=h.get("tags", ""), source="pixabay"))
    return out


# ---- Internet Archive: public-domain films, cut into short silent scenes ----
# Only films whose own license says public domain (or CC0) are used. Each film is downloaded once (small
# version), cut at its scene changes into 3-8 second pieces with no sound, and kept in the cache folder.
# A clip is named "archive://<film id>/<n>" and lives in DATA/archive/<film id>_<n>.mp4.
ARCHIVE_COLLECTIONS = "prelinger OR fedflix"
ARCHIVE_PER_FILM, ARCHIVE_MAX_MB, ARCHIVE_FILMS_PER_QUERY = 6, 90, 3
ARCHIVE_QUERIES = ["woman office", "women at work", "business meeting", "city street", "walking", "telephone",
                   "mirror", "family home", "dinner party", "manners etiquette", "train station", "crowd",
                   "clock time", "speaking audience", "young woman", "man at desk", "dancing party", "fashion",
                   "shopping store", "classroom students"]


def _archive_dir():
    from .paths import DATA
    d = os.path.join(DATA, "archive"); os.makedirs(d, exist_ok=True); return d


def archive_file(full):
    """Local file of an archive clip name, or None."""
    m = re.fullmatch(r"archive://([^/]+)/(\d+)", full or "")
    f = os.path.join(_archive_dir(), f"{m.group(1)}_{m.group(2)}.mp4") if m else None
    return f if f and os.path.exists(f) else None


def archive_credit(full):
    """(film title, link) of an archive clip, for the record of where each clip came from."""
    m = re.fullmatch(r"archive://([^/]+)/(\d+)", full or "")
    if not m: return None
    try: idx = json.load(open(os.path.join(_archive_dir(), "index.json")))
    except Exception: idx = {}
    return idx.get(m.group(1), {}).get("title", m.group(1)), "https://archive.org/details/" + m.group(1)


def _ffmpeg():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or "ffmpeg"


def _cut_film(path, ident):
    """Cuts a film into short silent scenes. Returns how many pieces were made."""
    ff, d = _ffmpeg(), _archive_dir()
    r = subprocess.run([ff, "-hide_banner", "-i", path, "-t", "1500", "-vf", "scale=320:-2,select='gt(scene,0.3)',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    cuts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", r)]
    dur = re.findall(r"Duration: (\d+):(\d+):([\d.]+)", r)
    total = (int(dur[0][0]) * 3600 + int(dur[0][1]) * 60 + float(dur[0][2])) if dur else (cuts[-1] if cuts else 0)
    total = min(total, 1500)
    if total < 20: return 0
    edges = [0.0] + cuts + [total]
    segs = []
    for a, b in zip(edges, edges[1:]):
        a2 = a + 0.4   # skip the flash right after a cut
        if b - a2 >= 3.0 and total * 0.07 < a2 < total * 0.93: segs.append((a2, min(b - a2 - 0.2, 8.0)))
    if not segs: return 0
    m = min(ARCHIVE_PER_FILM, len(segs))
    pick = [segs[round(k * (len(segs) - 1) / max(m - 1, 1))] for k in range(m)] if m > 1 else segs[:1]
    pick = [x for i, x in enumerate(pick) if x not in pick[:i]]
    made = 0
    for n, (start, length) in enumerate(pick):
        out = os.path.join(d, f"{ident}_{n}.mp4")
        subprocess.run([ff, "-loglevel", "error", "-y", "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", path, "-an",
                        "-vf", "scale=720:-2:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-c:v", "libx264", "-crf", "27", "-preset", "veryfast", "-pix_fmt", "yuv420p", out],
                       capture_output=True)
        if os.path.exists(out) and os.path.getsize(out) > 5000: made += 1
        elif os.path.exists(out): os.remove(out)
    return made


def _archive_film(doc):
    """Makes the clips of one film (once; remembered on disk). Returns the clip dicts."""
    ident, title = doc["identifier"], doc.get("title") or doc["identifier"]
    if isinstance(title, list): title = title[0]
    d = _archive_dir(); done = os.path.join(d, ident + ".done")
    if not os.path.exists(done):
        meta = S.get(f"https://archive.org/metadata/{ident}", timeout=40).json()
        files = [f for f in meta.get("files", []) if f.get("name", "").lower().endswith(".mp4")
                 and 1_000_000 < int(f.get("size") or 0) < ARCHIVE_MAX_MB * 1_000_000]
        if not files: open(done, "w").write("0"); return []
        pref = lambda f: (0 if "512" in f.get("format", "") else 1, int(f["size"]))   # the small 512Kb version first
        f = sorted(files, key=pref)[0]
        tmp = os.path.join(d, ident + ".src.mp4")
        with S.get(f"https://archive.org/download/{ident}/" + urllib.parse.quote(f["name"]), stream=True, timeout=90) as r:
            if r.status_code != 200: return []
            with open(tmp, "wb") as o:
                for chunk in r.iter_content(1 << 20): o.write(chunk)
        n = _cut_film(tmp, ident); os.remove(tmp)
        try: idx = json.load(open(os.path.join(d, "index.json")))
        except Exception: idx = {}
        idx[ident] = dict(title=title); json.dump(idx, open(os.path.join(d, "index.json"), "w"))
        open(done, "w").write(str(n))
    desc = " ".join(str(x) for x in [title, " ".join(doc["subject"]) if isinstance(doc.get("subject"), list) else doc.get("subject", "")])
    out = []
    for n in range(ARCHIVE_PER_FILM):
        f = os.path.join(d, f"{ident}_{n}.mp4")
        if os.path.exists(f):
            out.append(dict(full=f"archive://{ident}/{n}", small=f"archive://{ident}/{n}", desc=desc, source="archive"))
    return out


def archive(q, n, key=None):
    """Public-domain films from the Internet Archive (Prelinger and FedFlix collections), as short silent scenes."""
    r = S.get("https://archive.org/advancedsearch.php", timeout=40, params={
        "q": f"({q}) AND collection:({ARCHIVE_COLLECTIONS}) AND mediatype:movies", "rows": 12, "output": "json",
        "fl[]": ["identifier", "title", "licenseurl", "subject", "downloads"], "sort[]": "downloads desc"}).json()
    out, films = [], 0
    for doc in r.get("response", {}).get("docs", []):
        lic = (doc.get("licenseurl") or "").lower()
        if "publicdomain" not in lic and "/zero/" not in lic: continue   # only films that say public domain / CC0
        try: out += _archive_film(doc)
        except Exception as e: print("archive film skipped:", doc.get("identifier"), e, flush=True)
        films += 1
        if films >= ARCHIVE_FILMS_PER_QUERY or len(out) >= n: break
    return out


# id: (name shown in the app, search function, needs a key, where to get the key)
SOURCES = {
    "tenor": ("Tenor (GIF clips)", tenor, False, ""),
    "giphy": ("Giphy (GIF clips)", giphy, True, "https://developers.giphy.com/dashboard/"),
    "pexels": ("Pexels (real video)", pexels, True, "https://www.pexels.com/api/"),
    "pixabay": ("Pixabay (real video)", pixabay, True, "https://pixabay.com/api/docs/"),
    "archive": ("Internet Archive (public-domain films)", archive, False, ""),
}
