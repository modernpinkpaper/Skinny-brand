"""Builds timeline.json + audio.wav for the new-hire video (Sally explains a day on the print team).

  python build_nh.py <work folder with voice/*.wav>

Places each narration line, starts a new illustrated step when the topic changes, syncs the mouth to the voice,
times the captions from the real audio, adds small sound effects, and mixes the audio."""
import os, sys, json, math, re
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "skits", "animation"))
import build as sk            # sound effects, Track, word_times, SR, FPS
SR, FPS = sk.SR, sk.FPS


def main():
    work = sys.argv[1]; vdir = os.path.join(work, "voice")
    L = json.load(open(os.path.join(HERE, "lines.json")))["lines"]
    voice, sfx = sk.Track(), sk.Track()
    wav, dur = {}, {}
    for l in L:
        a, sr = sf.read(os.path.join(vdir, l["id"] + ".wav"), dtype="float32"); assert sr == SR
        wav[l["id"]] = a; dur[l["id"]] = len(a) / SR
    scenes, expr, poses, trans, placed = [], [], [], [], []
    t = 0.0; cur = None; LEAD = 0.55
    for i, l in enumerate(L):
        if l["scene"] != cur:                                     # a new illustrated step starts
            if scenes: scenes[-1]["end"] = t
            scenes.append(dict(look=l["scene"], start=t, chip=l["chip"])); cur = l["scene"]
            if i:
                sfx.put(t - .05, sk.sfx_whoosh(.4), .5); trans.append(dict(t=t, flash=.55, whip=0))
                sfx.put(t + .15, sk.sfx_ding(), .35)
            t += LEAD
        s0, e0 = t, t + dur[l["id"]]; placed.append((l, s0, e0)); voice.put(s0, wav[l["id"]], 1.0)
        expr.append(dict(t=round(s0 - .05, 3), expr=l["expr"])); poses.append(dict(t=round(s0 - .15, 3), pose=l["pose"]))
        if l["gap"] >= .6: expr.append(dict(t=round(e0 + .2, 3), expr="poised"))
        t = e0 + l["gap"]
    end = t + 1.2; scenes[-1]["end"] = end
    expr.sort(key=lambda e: e["t"]); poses.sort(key=lambda p: p["t"])
    # mouth from the voice
    n = int(math.ceil(end * FPS)) + 2; hop = SR // FPS; env = np.zeros(n, np.float32)
    for f in range(n):
        seg = voice.a[f * hop:(f + 1) * hop]; env[f] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    ref = np.percentile(env[env > 0.004], 85) if (env > 0.004).any() else 1
    m = np.clip(env / ref, 0, 1) ** .8; m[env < .004] = 0; sm = np.zeros_like(m); v = 0
    for i, x in enumerate(m): v = x if x > v else v * .6 + x * .4; sm[i] = v
    # captions: real word timings, bursts of up to 5 words
    phrases = []
    for l, s0, e0 in placed:
        words = l["text"].replace("R A", "RA").split(); real = sk.word_times(os.path.join(vdir, l["id"] + ".wav"), words)
        if real is None:
            wt = [len(re.sub(r"\W", "", w)) + 1.5 + (2.5 if re.search(r"[.?!]$", w) else 0) for w in words]; tot = sum(wt); acc = 0; real = []
            for x in wt: real.append(((e0 - s0) * acc / tot, (e0 - s0) * (acc + x) / tot)); acc += x
        W = [dict(w=w, s=round(s0 + a, 3), e=round(s0 + b, 3)) for w, (a, b) in zip(words, real)]
        parts = max(1, math.ceil(len(W) / 5)); size = math.ceil(len(W) / parts)
        for k in range(parts):
            part = W[k * size:(k + 1) * size]
            if part: phrases.append(dict(s=part[0]["s"], e=part[-1]["e"], words=part))
    tl = dict(fps=FPS, duration=end, scenes=scenes, expr=expr, poses=poses, mouth=[round(float(x), 3) for x in sm],
              hairUp=-1, hairDown=99999, tieOff=-1, tieBack=1e9, reject=0, formAt=0, punch=[], shake=[], zoom=[],
              transitions=trans, phrases=phrases, premise=[])
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"))
    L_ = int(end * SR) + SR; mix = voice.a[:L_] + sfx.a[:L_] * .55
    sf.write(os.path.join(work, "audio.wav"), mix / max(1.0, np.abs(mix).max() / .95), SR)
    print(f"timeline ok: {end:.1f}s ({end/60:.1f} min), {len(placed)} lines, {len(scenes)} scenes, voice {sum(dur.values()):.1f}s")


if __name__ == "__main__":
    main()
