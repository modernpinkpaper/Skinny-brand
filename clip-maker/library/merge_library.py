"""Joins the shards into one library: removes duplicates, tags each clip animated or real, writes
library.json + library.npz (+ library.zip with both, which the app downloads).

  python library/merge_library.py shards_dir out_dir"""
import os, sys, json, glob, zipfile, time
import numpy as np, torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from clipmaker import picker

src, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
clips, embs, seen, rejected = [], [], set(), 0
for js in sorted(glob.glob(os.path.join(src, "**", "shard-*[0-9].json"), recursive=True)):
    meta = json.load(open(js)); emb = np.load(js[:-5] + ".npz")["emb"]
    rej = js[:-5] + "-rejected.json"
    if os.path.exists(rej): rejected += len(json.load(open(rej)))
    for c, e in zip(meta, emb):
        if c["full"] in seen: continue
        seen.add(c["full"]); clips.append(c); embs.append(e)
E = np.stack(embs).astype(np.float32); E /= np.linalg.norm(E, axis=1, keepdims=True)

# animated or real? (same CLIP test the app uses)
T = picker.txt_emb(picker.CARTOON + picker.REAL).numpy()
p = torch.from_numpy(100 * E @ T.T).softmax(-1).numpy()[:, :len(picker.CARTOON)].sum(1)
for c, v in zip(clips, p):
    c["cartoon"] = round(float(v), 3)
    c["kind"] = "animated" if v >= 0.75 else "real" if v <= 0.3 else "mixed"

info = dict(built=time.strftime("%Y-%m-%d"), clips=len(clips), rejected=rejected,
            animated=sum(c["kind"] == "animated" for c in clips), real=sum(c["kind"] == "real" for c in clips))
json.dump(dict(info=info, clips=clips), open(os.path.join(out, "library.json"), "w"))
np.savez_compressed(os.path.join(out, "library.npz"), emb=E.astype(np.float16))
with zipfile.ZipFile(os.path.join(out, "library.zip"), "w", zipfile.ZIP_DEFLATED) as z:
    z.write(os.path.join(out, "library.json"), "library.json"); z.write(os.path.join(out, "library.npz"), "library.npz")
print(json.dumps(info), flush=True)
