"""Makes a video from a script file - the same steps as the app's Make video button, no window needed.
Used by the "Make video" workflow on GitHub when a file is added to clip-maker/scripts/.

  python make_from_file.py scripts/my-video.txt --out out/

The file is your script. Settings are optional; put them at the top and end them with a line of three dashes:
    look: moody            (moody, bright, vintage, black and white, pastel, none)
    clips: animated        (animated, real, both)
    speed: a bit slower    (normal, a bit slower, slower)
    end: send this to someone who needs to hear it     (end: none = no end screen)
    tags: #healing #selflove
    ---
    First line of the script
    ...
Voice marks (optional, see VOICE-DIRECTIONS.md): [sad, slow] at the start of a line, *word* to lean on a word,
(pause) or (long pause) inside a line."""
import os, sys, re, json, time, shutil, argparse, threading

LOOK_WORDS = {"moody": "moody", "muted": "moody", "dark": "moody", "bright": "bright", "colorful": "bright",
              "colourful": "bright", "vintage": "vintage", "warm": "vintage", "nostalgic": "vintage",
              "black": "bw", "bw": "bw", "b&w": "bw", "white": "bw", "pastel": "pastel", "dreamy": "pastel",
              "soft": "pastel", "none": "none", "any": "none", "no": "none"}
DEFAULTS = dict(look="moody", clips="animated", speed=0.92, end="send this to someone who needs to hear it",
                tags="#healing #selflove #relatable #fyp", live=False)


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
            elif k == "live":
                opts["live"] = v.lower() in ("yes", "true", "on", "1")
    return script, opts


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("file"); ap.add_argument("--out", default="out")
    args = ap.parse_args()
    from clipmaker import picker, render, library, direct
    from clipmaker.paths import VOICES, device_name
    script, o = read_file(args.file)
    lines, breaks, dirs = direct.parse(script)   # voice marks: [sad, slow], *word*, (pause)
    if not lines: sys.exit(f"{args.file}: no script lines found")
    name = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(os.path.basename(args.file))[0].lower()).strip("-") or "video"
    say = lambda p, m: print(f"[{p:5.1f}%] {m}", flush=True)
    print(f"{name}: {len(lines)} lines, look={o['look']}, clips={o['clips']}, speed={o['speed']}, voice marks={'yes' if direct.has_marks(dirs) else 'no'}, using {device_name()}",
          flush=True)
    t0 = time.time()
    library.update()
    import torch, torchaudio, transformers, chatterbox.tts, faster_whisper, noisereduce, rapidocr_onnxruntime  # noqa
    ref = VOICES["guy"][1]
    voice = dict(result=None, error=None)
    def make_voice():
        try: voice["result"] = render.make_voice(lines, breaks, o["end"], ref, o["speed"], lambda p, m: None, dirs)
        except Exception as e: voice["error"] = e
    vt = threading.Thread(target=make_voice); vt.start()   # the voice is made while the clips are found
    cands = picker.find_clips(lines, ["tenor"], {}, o["clips"], o["look"], lambda p, m: say(p * 0.5, m), live=o["live"])
    say(50, "clips picked, waiting for the voice"); vt.join()
    if voice["error"]: raise voice["error"]
    proj = os.path.join(args.out, name); os.makedirs(proj, exist_ok=True)
    video = render.build(proj, name, lines, breaks, cands, o["end"], o["look"], ref, o["tags"],
                         lambda p, m: say(50 + p * 0.5, m), audio_parts=voice["result"], dirs=dirs)
    json.dump(dict(name=name, lines=len(lines), settings=o, seconds=round(time.time() - t0)),
              open(os.path.join(proj, "info.json"), "w"), indent=1)
    shutil.rmtree(os.path.join(proj, "clips"), ignore_errors=True)
    print(f"DONE {video} in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
