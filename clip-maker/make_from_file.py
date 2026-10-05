"""Makes a video from a script file - the same steps as the app's Make video button, no window needed.
Used by the "Make video" workflow on GitHub when a file is added to clip-maker/scripts/.

  python make_from_file.py scripts/my-video.txt --out out/

The file is your script. Settings are optional; put them at the top and end them with a line of three dashes:
    look: moody            (moody, bright, vintage, black and white, pastel, none)
    clips: animated        (animated, real, both)
    sources: archive       (tenor, archive, illustration; archive = public-domain films, illustration = couture drawings; default tenor)
    speed: a bit slower    (normal, a bit slower, slower)
    length: natural        (61 = hold the end screen until 61 s for TikTok pay, the default; natural = as long as the script)
    bars: f3ead9           (colour of the bars above and below the picture; default near-black)
    voice: guy             (guy = the sample voice; posh = the model's own calm, poised built-in voice)
    end: send this to someone who needs to hear it     (end: none = no end screen)
    tags: #healing #selflove
    ---
    First line of the script
    ..."""
import os, sys, re, json, time, shutil, argparse, threading

LOOK_WORDS = {"moody": "moody", "muted": "moody", "dark": "moody", "bright": "bright", "colorful": "bright",
              "colourful": "bright", "vintage": "vintage", "warm": "vintage", "nostalgic": "vintage",
              "black": "bw", "bw": "bw", "b&w": "bw", "white": "bw", "pastel": "pastel", "dreamy": "pastel",
              "soft": "pastel", "none": "none", "any": "none", "no": "none"}
DEFAULTS = dict(look="moody", clips="animated", speed=1.0, end="send this to someone who needs to hear it",
                tags="#healing #selflove #relatable #fyp", live=False, sources=["tenor"], voice="guy", length="61", bars="080808")


def read_file(path):
    text = open(path, encoding="utf-8-sig").read().replace("\r\n", "\n")
    opts, script = dict(DEFAULTS), text
    parts = re.split(r"(?m)^\s*-{3,}\s*$", text, maxsplit=1)
    if len(parts) == 2:
        script = parts[1]
        for line in parts[0].splitlines():
            if ":" not in line: continue
            k, v = [x.strip() for x in line.split(":", 1)]; k = k.lower()
            if k == "look":
                opts["look"] = next((LOOK_WORDS[w] for w in re.findall(r"[a-z&]+", v.lower()) if w in LOOK_WORDS), "moody")
            elif k in ("clips", "clip", "type"):
                v = v.lower(); opts["clips"] = "both" if "both" in v else "real" if "real" in v else "animated"
            elif k == "speed":
                v = v.lower()
                opts["speed"] = 1.0 if "normal" in v else 0.85 if v.startswith("slower") or v == "slow" else \
                    float(v) if re.fullmatch(r"[\d.]+", v) else 0.92
            elif k == "end":
                opts["end"] = "" if v.lower() in ("none", "no", "off", "") else v
            elif k in ("tags", "hashtags"):
                opts["tags"] = v
            elif k == "length":
                opts["length"] = "natural" if any(w in v.lower() for w in ("natural", "short", "none", "no")) else "61"
            elif k == "bars":
                m = re.search(r"#?([0-9a-fA-F]{6})", v); opts["bars"] = m.group(1) if m else "080808"
            elif k == "voice":
                opts["voice"] = "posh" if any(w in v.lower() for w in ("posh", "lady", "default", "female", "woman", "rich")) else "guy"
            elif k in ("sources", "source"):
                found = [w for w in ("tenor", "archive", "illustration") if w in v.lower()]
                if found: opts["sources"] = found
            elif k == "live":
                opts["live"] = v.lower() in ("yes", "true", "on", "1")
    return script, opts


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--out", default="out")
    args = ap.parse_args()
    from clipmaker import picker, render, library
    from clipmaker.paths import VOICES, device_name
    script, o = read_file(args.file)
    lines, breaks = picker.parse_script(script)
    if not lines: sys.exit(f"{args.file}: no script lines found")
    name = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(args.file))[0].lower()).strip("-") or "video"
    say = lambda p, m: print(f"[{p:5.1f}%] {m}", flush=True)
    print(f"{name}: {len(lines)} lines, look={o['look']}, clips={o['clips']}, sources={o['sources']}, speed={o['speed']}, using {device_name()}",
          flush=True)
    t0 = time.time()
    library.update()
    import torch, torchaudio, transformers, chatterbox.tts, faster_whisper, rapidocr_onnxruntime  # noqa
    from clipmaker import render as _r
    if o["length"] == "natural": _r.MIN_SECONDS = 0.0   # no padding to 61 s: the video is as long as the script
    _r.BARS = o["bars"]
    ref = VOICES["guy"][1]
    if o["voice"] == "posh":   # the model's own built-in voice, slower and more poised than the guy's
        from clipmaker import voice as _v
        ref = None; _v.STYLE.update(exaggeration=0.4, cfg_weight=0.25)
    voice = dict(result=None, error=None)
    def make_voice():
        try: voice["result"] = render.make_voice(lines, breaks, o["end"], ref, o["speed"], lambda p, m: None)
        except Exception as e: voice["error"] = e
    vt = threading.Thread(target=make_voice); vt.start()   # the voice is made while the clips are found
    cands = picker.find_clips(lines, o["sources"], {}, o["clips"], o["look"], lambda p, m: say(p * 0.5, m), live=o["live"])

    say(50, "clips picked, waiting for the voice"); vt.join()
    if voice["error"]: raise voice["error"]
    proj = os.path.join(args.out, name); os.makedirs(proj, exist_ok=True)
    video = render.build(proj, name, lines, breaks, cands, o["end"], o["look"], ref, o["tags"],
                         lambda p, m: say(50 + p * 0.5, m), audio_parts=voice["result"])
    picker.remember_use([c[0]["full"] for c in cands if c], name)   # so the next videos pick other clips
    from clipmaker.sources import archive_credit   # where every public-domain film clip came from
    credits = sorted({archive_credit(c[0]["full"]) for c in cands if c and archive_credit(c[0]["full"])})
    json.dump(dict(name=name, lines=len(lines), settings=o, seconds=round(time.time() - t0),
                   archive_films=[dict(title=t, link=u) for t, u in credits]),
              open(os.path.join(proj, "info.json"), "w"), indent=1)
    shutil.rmtree(os.path.join(proj, "clips"), ignore_errors=True)
    print(f"DONE {video} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
