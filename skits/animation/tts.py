"""Makes the skit's voice lines with Chatterbox, using the owner's own tone samples as the voice reference.

  python tts.py <folder with the tone .wav files> <out folder> [line ids...]

Steps per line: pick the tone sample (calm / warm / energetic / expressive / upset), generate with that line's
expressiveness, raise the pitch (formant kept) toward the target performer's brighter pitch, set the level, trim silence.
The voice samples stay on this computer; nothing here uploads them."""
import os, sys, json, glob, subprocess, shutil

HERE = os.path.dirname(os.path.abspath(__file__))


def ffmpeg(*a): subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


def clean_refs(src, out):
    """The tone samples carry a low rumble under the voice. Remove it so it can't leak into the clone."""
    os.makedirs(out, exist_ok=True); refs = {}
    for f in glob.glob(os.path.join(src, "*voice-tone-*.wav")):
        name = os.path.basename(f).split("voice-tone-")[1].split(".")[0]
        dst = os.path.join(out, name + ".wav")
        ffmpeg("-i", f, "-af", "highpass=f=90,loudnorm=I=-20:TP=-2", "-t", "12", "-ar", "24000", "-ac", "1", dst)
        refs[name] = dst
    return refs


def post(L, raw_file, final):
    """Raise the pitch (formant kept), then cut the rumble again (the shift moves it up), set the level, trim silence."""
    ratio = 2 ** (L["pitch"] / 12)
    ffmpeg("-i", raw_file, "-af",
           f"highpass=f=120,rubberband=tempo={L.get('tempo',1.0):.3f}:pitch={ratio:.4f}:formant=preserved,highpass=f=110,volume={L['gain']}dB,"
           "silenceremove=start_periods=1:start_threshold=-45dB:stop_periods=1:stop_threshold=-45dB:stop_duration=0.25",
           "-ar", "24000", "-ac", "1", os.path.join(final, L["id"] + ".wav"))


def main():
    src, out = sys.argv[1], sys.argv[2]; only = set(a for a in sys.argv[3:] if not a.startswith("--"))
    lines = json.load(open(os.path.join(HERE, "lines.json")))["lines"]
    if "--post-only" in sys.argv:   # re-run just the pitch / level step on lines already generated
        for L in lines:
            if not only or L["id"] in only: post(L, os.path.join(out, "raw", L["id"] + ".wav"), os.path.join(out, "voice"))
        return
    refs = clean_refs(src, os.path.join(out, "refs")); raw = os.path.join(out, "raw"); os.makedirs(raw, exist_ok=True)
    final = os.path.join(out, "voice"); os.makedirs(final, exist_ok=True)
    import torch, torchaudio
    from chatterbox.tts import ChatterboxTTS
    model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")
    for L in lines:
        if only and L["id"] not in only: continue
        torch.manual_seed(7)   # same take every time, so edits don't change lines you already liked
        w = model.generate(L["text"], audio_prompt_path=refs[L["ref"]], exaggeration=L["exaggeration"], cfg_weight=L["cfg"])
        r = os.path.join(raw, L["id"] + ".wav"); torchaudio.save(r, w.cpu(), model.sr)
        post(L, r, final)
        print("made", L["id"], L["text"][:40], flush=True)


if __name__ == "__main__":
    main()
