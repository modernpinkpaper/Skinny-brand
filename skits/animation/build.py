"""Builds the timeline (timeline.json) and the mixed audio (audio.wav) for the skit animation.

  python build.py <work folder that holds voice/*.wav>

Reads lines.json, places each voice line, syncs the mouth to the voice, makes the sound effects, mixes everything."""
import os, sys, json, math, re
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__)); SR = 24000; FPS = 30
rng = np.random.default_rng(3)

def tone(f, d, shape="sin", decay=6.0, amp=1.0):
    t = np.arange(int(d * SR)) / SR
    w = np.sin(2 * np.pi * f * t) if shape == "sin" else np.sign(np.sin(2 * np.pi * f * t))
    return (w * np.exp(-decay * t) * amp).astype(np.float32)

def noise(d, lo=None, hi=None):
    n = rng.standard_normal(int(d * SR)).astype(np.float32)
    if lo or hi:
        S = np.fft.rfft(n); fr = np.fft.rfftfreq(len(n), 1 / SR); m = np.ones_like(fr)
        if lo: m[fr < lo] = 0
        if hi: m[fr > hi] = 0
        n = np.fft.irfft(S * m, len(n)).astype(np.float32)
    return n / (np.abs(n).max() + 1e-9)

def sfx_buzz():     # phone vibrating twice
    one = (tone(140, .28, "sq", 0, .5) * np.hanning(int(.28 * SR))).astype(np.float32); gap = np.zeros(int(.12 * SR), np.float32)
    return np.concatenate([one, gap, one, gap, one])
def sfx_tap():      return (noise(.05, 1500, 5000) * np.exp(-np.arange(int(.05 * SR)) / SR * 90) * .8).astype(np.float32)
def sfx_snap():     return np.concatenate([(noise(.03, 800, 6000) * .9), tone(220, .12, "sin", 30, .5)]).astype(np.float32)
def sfx_whoosh(d=.45):
    n = noise(d, 300, 6000); env = np.sin(np.linspace(0, np.pi, len(n))) ** 2; return (n * env * .8).astype(np.float32)
def sfx_ding():     return (tone(1320, .6, "sin", 5, .6) + tone(1980, .6, "sin", 7, .3)).astype(np.float32)
def sfx_cha():
    a = tone(2093, .35, "sin", 8, .5) + tone(3136, .35, "sin", 9, .3); b = tone(2637, .6, "sin", 5, .5) + tone(3951, .6, "sin", 6, .3)
    return np.concatenate([a, np.zeros(int(.08 * SR), np.float32), b]).astype(np.float32)
def sfx_pop():      return (tone(500, .12, "sin", 25, .7) * (1 + np.linspace(0, 1, int(.12 * SR)))).astype(np.float32)
def sfx_womp():     # sad two-note slide, quiet and short
    out = []
    for f0, f1, d in ((300, 230, .4), (260, 150, .7)):
        t = np.arange(int(d * SR)) / SR; f = np.linspace(f0, f1, len(t)); ph = 2 * np.pi * np.cumsum(f) / SR
        out.append((np.sin(ph) * np.exp(-2.2 * t) * .35).astype(np.float32))
    return np.concatenate(out)
def sfx_ring():     # phone ringing for the "RING!" burst
    b = tone(1050, .09, "sin", 0, .45) * np.hanning(int(.09 * SR)); g = np.zeros(int(.05 * SR), np.float32)
    return np.concatenate([b, g, b, g, b, g, b]).astype(np.float32)

class Track:
    def __init__(s): s.a = np.zeros(SR * 120, np.float32)
    def put(s, t, x, gain=1.0):
        i = int(t * SR); s.a[i:i + len(x)] += x * gain

def main():
    work = sys.argv[1]; vdir = os.path.join(work, "voice")
    L = json.load(open(os.path.join(HERE, "lines.json")))["lines"]
    voice, sfx = Track(), Track()
    dur = {}; wav = {}
    for l in L:
        a, sr = sf.read(os.path.join(vdir, l["id"] + ".wav"), dtype="float32"); assert sr == SR
        wav[l["id"]] = a; dur[l["id"]] = len(a) / SR
    scenes, expr, punch, shake, zoom, trans = [], [], [], [], [], []
    poses = [dict(t=0, pose="phone")]
    # gestures: (when, pose). when < 0 = that many seconds before the line; 0..1 = that fraction of the way through the line
    GEST = {"L0": [(0, "phone")], "L1": [(-.08, "ear")], "L3": [(-.1, "cup")], "L4": [(0, "open"), (.62, "point_l")],
            "L5": [(0, "laugh")], "L6": [(-.05, "clasp")], "L7": [(-.05, "offer")], "L8": [(-.1, "cup")], "L9": [(0, "chest")],
            "L10": [(-.1, "envelope")], "L11": [(0, "fan")], "L12": [(0, "chest")], "L13": [(-.05, "glass")], "L14": [(-.05, "wipe")]}
    placed = []                       # (line, start, end)
    PRE = {"call": 1.15, "interview": .55, "dayone": .55, "payday": .95, "promo": .5}
    # ---- opening: real life ----
    t = 0.0; scenes.append(dict(look="real", start=0.0)); expr.append(dict(t=0, expr="deadpan"))
    sfx.put(.55, sfx_tap(), .9)
    cur_scene = "real1"
    hair_up = None
    for l in L:
        if l["scene"] != cur_scene:
            if cur_scene == "real1":            # the hair-tie switch
                t += .25; sfx.put(t, sfx_snap(), 1.0); sfx.put(t + .08, sfx_whoosh(), .7)
                hair_up = t + .12; trans.append(dict(t=hair_up, flash=1.0, whip=1.0)); poses.append(dict(t=hair_up, pose="rest")); t = hair_up - .1
            else:
                sfx.put(t, sfx_whoosh(), .6); trans.append(dict(t=t + .1, flash=.55, whip=1.0))
            pre = PRE[l["scene"]]
            scenes[-1]["end"] = t + .1; scenes.append(dict(look=l["scene"], start=t + .1)); cur_scene = l["scene"]
            if l["scene"] == "call": sfx.put(t + .1, sfx_buzz(), .9); sfx.put(t + .1 + .55, sfx_ring(), .35); poses.append(dict(t=t + .1, pose="phone"))
            if l["scene"] == "payday": sfx.put(t + .6, sfx_cha(), .8)
            if l["scene"] == "promo": sfx.put(t + .1, sfx_pop(), .8)
            t += pre
        if l["scene"] == "call" and l["id"] == "L1": sfx.put(t - .05, sfx_tap(), .6)
        s0 = t; e0 = t + dur[l["id"]]; placed.append((l, s0, e0)); voice.put(s0, wav[l["id"]], 1.0)
        expr.append(dict(t=s0 - .05, expr=l["expr"]))
        for w, pz in GEST.get(l["id"], []): poses.append(dict(t=round(s0 + (w if w < 0 else w * dur[l["id"]]), 3), pose=pz))
        if l["expr"] in ("shocked", "gasp", "laugh"): punch.append(s0 + .05)
        if l["id"] in ("L3", "L8"): zoom.append([s0 - .1, e0 + .4, .09])
        if l["id"] == "L5": shake.append(s0 + .08)
        if l["id"] == "L14": shake.append(s0 + dur[l["id"]] * .5)
        t = e0 + l["gap"]
        if l["gap"] >= .5: expr.append(dict(t=e0 + .12, expr={"L0": "sigh", "L5": "shocked", "L11": "shocked", "L12": "smug"}.get(l["id"], "poised") if l["id"] in ("L0", "L5", "L11", "L12") else l["expr"]))
    # ---- back to real life ----
    t += .1; scenes[-1]["end"] = t; scenes.append(dict(look="real", start=t))
    trans.append(dict(t=t, flash=.0, whip=0.0)); sfx.put(t - .02, sfx_snap(), .5)
    expr.append(dict(t=t, expr="deadpan")); poses.append(dict(t=t, pose="phone"))
    sfx.put(t + .5, sfx_buzz(), .8); sfx.put(t + 1.5, sfx_ding(), .5)
    reject = t + 2.0; sfx.put(reject, sfx_womp(), .9)
    expr += [dict(t=t + 1.0, expr="camlook"), dict(t=t + 2.0, expr="frown"), dict(t=t + 4.3, expr="pout"),
             dict(t=t + 6.3, expr="sideeye"), dict(t=t + 8.3, expr="sigh")]
    form_at = t + 9.4; tie_back = form_at + .5; sfx.put(form_at, sfx_tap(), .9); sfx.put(tie_back, sfx_snap(), .9)
    expr.append(dict(t=form_at, expr="deadpan"))
    end = max(tie_back + 1.6, 61.6)
    scenes[-1]["end"] = end
    expr.sort(key=lambda e: e["t"]); poses.sort(key=lambda p: p["t"])
    # ---- mouth from the voice ----
    n = int(math.ceil(end * FPS)) + 2; env = np.zeros(n, np.float32); hop = SR // FPS
    for f in range(n):
        seg = voice.a[f * hop:(f + 1) * hop]
        env[f] = np.sqrt(np.mean(seg ** 2)) if len(seg) else 0
    ref = np.percentile(env[env > 0.004], 85) if (env > 0.004).any() else 1
    m = np.clip(env / ref, 0, 1) ** .8; m[env < .004] = 0
    sm = np.zeros_like(m); v = 0
    for i, x in enumerate(m):            # quick attack, slower release: reads like a mouth, not a flicker
        v = x if x > v else v * .6 + x * .4; sm[i] = v
    # ---- captions: one phrase per line (long lines split in two), word timing by letter count ----
    phrases = []
    for l, s0, e0 in placed:
        words = l["text"].split(); wt = [len(re.sub(r"\W", "", w)) + 1.5 + (2.5 if re.search(r"[.?!]$", w) else 0) for w in words]
        tot = sum(wt); acc = 0; W = []
        for w, x in zip(words, wt):
            a = s0 + (e0 - s0) * acc / tot; acc += x; b = s0 + (e0 - s0) * acc / tot; W.append(dict(w=w, s=round(a, 3), e=round(b, 3)))
        n_parts = max(1, math.ceil(len(W) / 5))   # short bursts of up to 5 words keep the text big
        size = math.ceil(len(W) / n_parts)
        for p in range(n_parts):
            part = W[p * size:(p + 1) * size]
            if part: phrases.append(dict(s=part[0]["s"], e=part[-1]["e"], words=part))
    tl = dict(fps=FPS, duration=end, scenes=scenes, expr=expr, poses=poses, mouth=[round(float(x), 3) for x in sm],
              hairUp=hair_up, hairDown=t, tieOff=hair_up, tieBack=tie_back, reject=reject, formAt=form_at,
              punch=punch, shake=shake, zoom=zoom, transitions=trans, phrases=phrases,
              premise=["me, 4 seconds after I hit submit", "on a job application"])
    json.dump(tl, open(os.path.join(work, "timeline.json"), "w"))
    # ---- mix ----
    L_ = int(end * SR) + SR; mix = np.zeros(L_, np.float32)
    mix += voice.a[:L_] * 1.0; mix += sfx.a[:L_] * .55
    sf.write(os.path.join(work, "audio.wav"), mix / max(1.0, np.abs(mix).max() / .95), SR)
    print(f"timeline ok: {end:.1f}s, {len(placed)} lines, voice {sum(dur.values()):.1f}s, hair up at {hair_up:.1f}s, back to reality at {t:.1f}s")

if __name__ == "__main__":
    main()
