"""Clip websites. Each search returns dicts: full (link to the clip), small (a small preview to check),
desc (words describing it), source. Tenor needs nothing; the others need a free key from their website."""
import re, urllib.parse, requests

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


# id: (name shown in the app, search function, needs a key, where to get the key)
SOURCES = {
    "tenor": ("Tenor (GIF clips)", tenor, False, ""),
    "giphy": ("Giphy (GIF clips)", giphy, True, "https://developers.giphy.com/dashboard/"),
    "pexels": ("Pexels (real video)", pexels, True, "https://www.pexels.com/api/"),
    "pixabay": ("Pixabay (real video)", pixabay, True, "https://pixabay.com/api/docs/"),
}
