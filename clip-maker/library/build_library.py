"""Builds one part ("shard") of the clip library. Runs on GitHub's computers - no AI chat involved.

  python library/build_library.py --shard 0 --shards 10 --out out/

For every search in its share of topics.queries(): search Tenor, then for each new clip download the small
preview for a moment and check it: does it really move, its colours/light, what the image checker (CLIP) sees,
and whether it has words on it (OCR). Only the data is kept, never the video. Output:
  shard-N.json   one entry per usable clip (link, description, look numbers, which search found it)
  shard-N.npz    the image-checker fingerprint of each clip (same order), 512 numbers each
  shard-N-rejected.json  clips thrown out and why (still image, words on it, white sticker)"""
import os, sys, json, time, argparse, tempfile
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clipmaker import picker
from clipmaker.sources import tenor, S
from clipmaker.motion import score as motion_score
from library.topics import queries

ap = argparse.ArgumentParser()
ap.add_argument("--shard", type=int, default=0); ap.add_argument("--shards", type=int, default=1)
ap.add_argument("--out", default="out"); ap.add_argument("--limit", type=int, default=0, help="only N searches (testing)")
ap.add_argument("--per-search", type=int, default=50)
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)
mine = [q for n, q in enumerate(queries()) if n % args.shards == args.shard]
if args.limit: mine = mine[:args.limit]
base = os.path.join(args.out, f"shard-{args.shard}")

# ---- 1. search (politely: one at a time, short wait) ----
found = {}
for n, q in enumerate(mine):
    for attempt in range(3):
        try:
            res = tenor(q, args.per_search); break
        except Exception as e:
            log("search failed, retrying:", q, e); time.sleep(5 * (attempt + 1)); res = []
    for c in res:
        if c["full"] not in found: c["q"] = q; found[c["full"]] = c
    if n % 20 == 0: log(f"searched {n + 1}/{len(mine)}: {len(found)} clips")
    time.sleep(0.4)
items = list(found.values())
log(f"{len(items)} clips to check")

# ---- 2. check each clip ----
tmp = tempfile.mkdtemp()
def prepare(c):
    """download preview -> movement -> 4 frames + colours. Returns (clip, frames) or (clip, reason)."""
    f = os.path.join(tmp, str(abs(hash(c["full"]))) + ".mp4")
    try:
        r = S.get(c["small"], timeout=40)
        if r.status_code != 200 or len(r.content) < 2000: return c, "download failed", None
        open(f, "wb").write(r.content)
        m = motion_score(f)[1]
        if m < 1.5: return c, "still image", f
        fr = picker._frames(f)
        if len(fr) < 2: return c, "unreadable", f
        c["motion"] = round(float(m), 2); c.update({k: round(v, 4) for k, v in picker._look_numbers(fr).items()})
        if c["white"] > 0.35: return c, "white sticker", f
        return c, fr, f
    except Exception as e:
        return c, f"error {e}", f

kept, embs, rejected = [], [], {}
def save():
    json.dump(kept, open(base + ".json", "w"))
    np.savez_compressed(base + ".npz", emb=np.stack(embs).astype(np.float16) if embs else np.zeros((0, 512), np.float16))
    json.dump(rejected, open(base + "-rejected.json", "w"))

batch = []
def flush():
    """CLIP fingerprints for a batch, then OCR; keeps the clips without words."""
    if not batch: return
    E = picker.img_emb([Image.fromarray(x) for _, fr, _ in batch for x in fr]).view(len(batch), -1, 512).mean(1)
    for (c, fr, f), e in zip(batch, E):
        text = picker.read_text(f)
        if picker.too_much_text(text): rejected[c["full"]] = "words: " + text[:60]
        else:
            c["checked"] = True; kept.append(c); embs.append(e.numpy())
        os.remove(f)
    batch.clear()

t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    for n, (c, res, f) in enumerate(ex.map(prepare, items)):
        if isinstance(res, str):
            rejected[c["full"]] = res
            if f and os.path.exists(f): os.remove(f)
        else:
            batch.append((c, res, f))
            if len(batch) >= 32: flush()
        if n % 200 == 0:
            rate = (n + 1) / (time.time() - t0)
            log(f"checked {n + 1}/{len(items)} ({rate:.1f}/s): kept {len(kept)}, rejected {len(rejected)}")
        if n % 1000 == 999: save()
flush(); save()
log(f"done: kept {len(kept)}, rejected {len(rejected)} -> {base}.json")
