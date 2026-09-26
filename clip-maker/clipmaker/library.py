"""The ready-made clip library (built on GitHub by library/build_library.py): links, looks and image
fingerprints of thousands of already-checked Tenor clips, so picking clips takes seconds instead of minutes.
Downloaded once, then checked for a newer version at most once a week."""
import os, json, time, zipfile, threading
import numpy as np
from .paths import DATA
from .sources import S

URL = "https://github.com/modernpinkpaper/Skinny-brand/releases/download/clip-library/library.zip"
DIR = os.path.join(DATA, "library"); os.makedirs(DIR, exist_ok=True)
STAMP = os.path.join(DIR, "downloaded.json")
_lock, _lib = threading.Lock(), None


def update(force=False):
    """Downloads the library if it's missing or a newer one was published (checked weekly). Never raises."""
    try:
        stamp = json.load(open(STAMP)) if os.path.exists(STAMP) else {}
        have = os.path.exists(os.path.join(DIR, "library.npz"))
        if have and not force and time.time() - stamp.get("checked", 0) < 7 * 86400: return
        head = S.head(URL, allow_redirects=True, timeout=30)
        if head.status_code != 200: return
        version = head.headers.get("ETag") or head.headers.get("Last-Modified") or head.headers.get("Content-Length")
        if have and version == stamp.get("version"):
            stamp["checked"] = time.time(); json.dump(stamp, open(STAMP, "w")); return
        r = S.get(URL, timeout=600)
        if r.status_code != 200: return
        z = os.path.join(DIR, "library.zip.part"); open(z, "wb").write(r.content)
        with zipfile.ZipFile(z) as f:
            for name in ("library.json", "library.npz"):
                open(os.path.join(DIR, name + ".part"), "wb").write(f.read(name))
        with _lock:
            for name in ("library.json", "library.npz"): os.replace(os.path.join(DIR, name + ".part"), os.path.join(DIR, name))
            global _lib; _lib = None
        os.remove(z)
        json.dump(dict(checked=time.time(), version=version), open(STAMP, "w"))
    except Exception as e:
        print("clip library update skipped:", e, flush=True)


def load():
    """(info, clips, fingerprints) or None when there is no library yet."""
    global _lib
    with _lock:
        if _lib is None and os.path.exists(os.path.join(DIR, "library.npz")):
            d = json.load(open(os.path.join(DIR, "library.json")))
            E = np.load(os.path.join(DIR, "library.npz"))["emb"].astype(np.float32)
            E /= np.linalg.norm(E, axis=1, keepdims=True) + 1e-6
            _lib = (d["info"], d["clips"], E)
        return _lib


def info():
    lib = load()
    return lib[0] if lib else None
