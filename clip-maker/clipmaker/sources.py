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
# Only films that are public domain: the film's own license says public domain / CC0, or it is a silent-era film
# from 1930 or earlier (US public domain by age). The films are a hand-picked list (elegant, high-society,
# glamour, grooming, "becoming her best self"), not free searches. A film is never downloaded whole: ffmpeg jumps to
# points spread through it over the network and cuts a few short silent scenes, which are kept in the cache folder.
# A clip is named "archive://<film id>/<n>" and lives in DATA/archive/<film id>_<n>.mp4.
ARCHIVE_SCENES = 10   # scenes cut from each film
ARCHIVE_FILMS = [
    # 1950s colour: glamour, fashion, grooming, manners
    "Designfo1956", "American1958", "American1958_2", "American1958_3", "Frigidai1957", "Technico1949",
    "TouchofM1961", "HowtoBeW1949", "BodyCare1948", "MuchAdoA1950", "GoodTabl1951", "CindyGoe1955",
    "JuniorPr1946", "UnionSqu1950", "ArrangingThe", "SocialCl1957", "Heritage1963", "Wordtoth1955",
    # silent era: society dramas, ballgowns, mansions, Cinderella stories
    "Why_Change_Your_Wife", "MaleAndFemale_201704", "ForBetterForWorseForYT", "silent-zaza", "silent-beyond-the-rocks",
    "Manslaughter_1922", "ThePoorLittleRichGirl", "LadyWindermeresFan", "silent-forbidden-paradise",
    "silent-a-woman-of-the-world", "silent-madame-dubarry", "silent-black-oxen", "silent-parisian-love", "The_Cheat",
    "1921Camille", "silent-a-kiss-for-cinderella", "silent-the-lady",
    "my-movie_20220215", "the-mysterious-lady-1928", "a-woman-of-affairs-1928",
    "silent-the-waiters-ball", 
]
ARCHIVE_QUERIES = ["id:" + i for i in dict.fromkeys(ARCHIVE_FILMS)]


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
    """The computer's own ffmpeg when there is one (best at reading from the internet), else the bundled one."""
    found = shutil.which("ffmpeg")
    if found: return found
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def _is_public_domain(meta):
    """The film's own license says public domain / CC0, or it is a silent-era film from 1930 or earlier."""
    lic = str(meta.get("licenseurl") or "").lower()
    if "publicdomain" in lic or "/zero/" in lic: return True
    coll = meta.get("collection") or []
    coll = [coll] if isinstance(coll, str) else coll
    m = re.search(r"\b(1[89]\d\d)\b", str(meta.get("year") or meta.get("date") or ""))
    return "silent_films" in coll and bool(m) and int(m.group(1)) <= 1930


def _longest_piece(f):
    """Start and length of the longest scene inside a short clip (cuts the film's own scene changes out)."""
    ff = _ffmpeg()
    r = subprocess.run([ff, "-hide_banner", "-i", f, "-vf", "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    dur = re.findall(r"Duration: (\d+):(\d+):([\d.]+)", r)
    total = (int(dur[0][0]) * 3600 + int(dur[0][1]) * 60 + float(dur[0][2])) if dur else 0
    edges = [0.0] + [float(x) for x in re.findall(r"pts_time:([\d.]+)", r)] + [total]
    best = max(((b - a, a) for a, b in zip(edges, edges[1:])), default=(0, 0))
    return best[1], best[0], total


def _cut_scenes(src, ident, length, netopt):
    """Cuts ARCHIVE_SCENES short silent scenes out of a film (a web link or a file). Returns how many were made."""
    ff, d, made = _ffmpeg(), _archive_dir(), 0
    if length <= 30: return 0
    lo, hi = length * 0.06, length * 0.92 - 8   # skip titles and credits
    for n in range(ARCHIVE_SCENES):
        t0 = lo + (hi - lo) * n / max(ARCHIVE_SCENES - 1, 1)
        raw, out = os.path.join(d, f"{ident}_{n}.raw.mp4"), os.path.join(d, f"{ident}_{n}.mp4")
        if os.path.exists(out): made += 1; continue
        subprocess.run([ff, "-loglevel", "error", "-y"] + netopt + ["-ss", f"{t0:.1f}", "-i", src, "-t", "8", "-an",
                        "-vf", "scale=720:-2:force_original_aspect_ratio=decrease,scale=trunc(iw/2)*2:trunc(ih/2)*2",
                        "-c:v", "libx264", "-crf", "27", "-preset", "veryfast", "-pix_fmt", "yuv420p", raw],
                       capture_output=True)
        if not os.path.exists(raw) or os.path.getsize(raw) < 5000: continue
        a, piece, _ = _longest_piece(raw)
        if piece >= 2.8:   # one scene only, without the film's own cuts
            subprocess.run([ff, "-loglevel", "error", "-y", "-ss", f"{a + 0.15:.2f}", "-t", f"{min(piece - 0.3, 8):.2f}",
                            "-i", raw, "-an", "-c:v", "libx264", "-crf", "27", "-preset", "veryfast", "-pix_fmt", "yuv420p", out],
                           capture_output=True)
            if os.path.exists(out) and os.path.getsize(out) > 5000: made += 1
            elif os.path.exists(out): os.remove(out)
        os.remove(raw)
    return made


def _archive_film(ident):
    """Makes the scenes of one film (once; remembered on disk). Returns the clip dicts."""
    d = _archive_dir(); done = os.path.join(d, ident + ".done")
    title = ident
    if not os.path.exists(done):
        meta = S.get(f"https://archive.org/metadata/{ident}", timeout=40).json()
        md = meta.get("metadata", {})
        title = md.get("title") or ident
        if isinstance(title, list): title = title[0]
        if not _is_public_domain(md):
            print("archive film skipped (not clearly public domain):", ident, flush=True)
            open(done, "w").write("0"); return []
        files = [f for f in meta.get("files", []) if f.get("name", "").lower().endswith(".mp4")
                 and f.get("source") == "derivative" and int(f.get("size") or 0) > 200_000]
        if not files:
            open(done, "w").write("0"); return []
        pref = lambda f: (0 if "512" in f.get("format", "") else 1, int(f["size"]))   # the small 512Kb version first
        f = sorted(files, key=pref)[0]
        url = f"https://archive.org/download/{ident}/" + urllib.parse.quote(f["name"])
        ff = _ffmpeg()
        ca = os.environ.get("REQUESTS_CA_BUNDLE") or os.environ.get("SSL_CERT_FILE")
        netopt = (["-ca_file", ca] if ca else [])
        try: length = float(f.get("length") or md.get("runtime") or 0)
        except ValueError: length = 0
        if not length:
            info = subprocess.run([ff, "-hide_banner"] + netopt + ["-i", url], capture_output=True, text=True).stderr
            t = re.findall(r"Duration: (\d+):(\d+):([\d.]+)", info)
            length = (int(t[0][0]) * 3600 + int(t[0][1]) * 60 + float(t[0][2])) if t else 0
        made = _cut_scenes(src=url, ident=ident, length=length, netopt=netopt)
        if made == 0 and int(f["size"]) <= 150_000_000:   # reading over the network did not work: download the file instead
            tmp = os.path.join(d, ident + ".src.mp4")
            try:
                with S.get(url, stream=True, timeout=90) as r:
                    if r.status_code == 200:
                        with open(tmp, "wb") as o:
                            for chunk in r.iter_content(1 << 20): o.write(chunk)
                        made = _cut_scenes(src=tmp, ident=ident, length=length, netopt=[])
            finally:
                if os.path.exists(tmp): os.remove(tmp)
        try: idx = json.load(open(os.path.join(d, "index.json")))
        except Exception: idx = {}
        idx[ident] = dict(title=title); json.dump(idx, open(os.path.join(d, "index.json"), "w"))
        if made: open(done, "w").write(str(made))   # nothing made = try again next time (e.g. the network failed)
    else:
        try: title = json.load(open(os.path.join(d, "index.json"))).get(ident, {}).get("title", ident)
        except Exception: pass
    out = []
    for n in range(ARCHIVE_SCENES):
        if os.path.exists(os.path.join(d, f"{ident}_{n}.mp4")):
            out.append(dict(full=f"archive://{ident}/{n}", small=f"archive://{ident}/{n}", desc=str(title), source="archive"))
    return out


def archive(q, n, key=None):
    """Public-domain film scenes from the Internet Archive. q is "id:<film id>" from the hand-picked list."""
    ident = q[3:] if q.startswith("id:") else None
    if not ident: return []
    try: return _archive_film(ident)
    except Exception as e:
        print("archive film skipped:", ident, e, flush=True); return []


# ---- Couture illustrations: each drawing in assets/illustrations/ becomes several short animated clips ----
# A slow zoom and pan over a different part of the drawing (hat, face, gloves, gown, hem) = one clip, so a few
# drawings give many different clips. Kept in the same cache folder as the film scenes (names start with "illus-").
ILLUS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "illustrations")
ILLUS_CROPS = [(0.10, 0.2), (0.28, 0.8), (0.46, 0.3), (0.64, 0.7), (0.82, 0.25), (0.95, 0.75)]   # (how far down, pan)
ILLUS_SECONDS = 6


def illustration(q, n, key=None):
    """Animated clips from the couture drawings in assets/illustrations/."""
    d, ff, out = _archive_dir(), _ffmpeg(), []
    if not os.path.isdir(ILLUS_DIR): return []
    try: idx = json.load(open(os.path.join(d, "index.json")))
    except Exception: idx = {}
    for fn in sorted(os.listdir(ILLUS_DIR)):
        if not fn.lower().endswith((".png", ".jpg", ".jpeg")): continue
        stem = re.sub(r"[^A-Za-z0-9]+", "-", os.path.splitext(fn)[0]).strip("-").lower()
        ident = "illus-" + stem
        src = os.path.join(ILLUS_DIR, fn)
        for k, (down, pan) in enumerate(ILLUS_CROPS):
            f = os.path.join(d, f"{ident}_{k}.mp4")
            if not os.path.exists(f):
                # take a 4:3 band at the chosen height, then zoom slowly and drift sideways inside it
                frames = ILLUS_SECONDS * 25
                vf = (f"scale=1888:-2,crop=1888:1416:0:'(ih-1416)*{down}',"
                      f"zoompan=z='1+0.22*on/{frames}':x='(iw-iw/zoom)*({pan}+0.25*on/{frames})':y='(ih-ih/zoom)*0.5':"
                      f"d={frames}:s=960x720:fps=25,format=yuv420p")
                subprocess.run([ff, "-loglevel", "error", "-y", "-loop", "1", "-i", src, "-vf", vf, "-t", str(ILLUS_SECONDS),
                                "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", f], capture_output=True)
            if os.path.exists(f) and os.path.getsize(f) > 5000:
                out.append(dict(full=f"archive://{ident}/{k}", small=f"archive://{ident}/{k}",
                                desc="couture fashion illustration of an elegant woman", source="illustration"))
        idx[ident] = dict(title=f"Couture illustration ({stem})")
    json.dump(idx, open(os.path.join(d, "index.json"), "w"))
    return out


# which searches each source runs (the picker uses its own list instead of the script's words)
SOURCE_QUERIES = {"archive": ARCHIVE_QUERIES, "illustration": ["illus:all"]}


# id: (name shown in the app, search function, needs a key, where to get the key)
SOURCES = {
    "tenor": ("Tenor (GIF clips)", tenor, False, ""),
    "giphy": ("Giphy (GIF clips)", giphy, True, "https://developers.giphy.com/dashboard/"),
    "pexels": ("Pexels (real video)", pexels, True, "https://www.pexels.com/api/"),
    "pixabay": ("Pixabay (real video)", pixabay, True, "https://pixabay.com/api/docs/"),
    "archive": ("Internet Archive (public-domain films)", archive, False, ""),
    "illustration": ("Couture illustrations (assets/illustrations)", illustration, False, ""),
}
