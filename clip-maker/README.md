# Clip Maker

Paste a script and get a finished TikTok video: a clip for every line, the voice, and the words typed on screen. No AI chat is needed. Everything runs on your own computer.

## Using it (Windows)
1. Download **ClipMaker-Windows.zip** (see "Getting the .exe" below) and unzip it anywhere, for example your Desktop.
2. Open the `ClipMaker` folder and double-click **ClipMaker.exe**. A black window opens (keep it open) and the app opens in your web browser.
3. Paste your script. One line = one clip. Leave a blank line where the voice should pause.
4. Choose the websites, the type of clips, the look and the voice, then press **Make video**.
5. It finds the clips and builds the video in one go. When it's done, the video plays in the app. Press **Open folder** to find the file.

Videos are saved in `Documents\Clip Maker\<video name>\`, with the voiceover (.wav) and `caption.txt`.

**The first time** you find clips or build a video, the app downloads its AI parts once (about 3 GB), so the first run takes longer.

**How long it takes** on a normal PC without an NVIDIA graphics card:
- Finding clips: about 10 minutes (faster when it has seen the clips before).
- Building a video: about 10 to 20 minutes, most of it making the voice.

**Have an NVIDIA graphics card?** Download **ClipMaker-Windows-NVIDIA** instead. It's a bigger download, but it uses the NVIDIA card, so the voice takes about 1 to 2 minutes instead of 10 to 20. The normal **ClipMaker-Windows** uses only the processor, even on a PC with NVIDIA.

The black window says what it's using, for example `Using: NVIDIA graphics card: GeForce RTX 3050`. If the NVIDIA build says "processor only", update your NVIDIA driver (GeForce Experience or nvidia.com/drivers). On a laptop, keep it plugged in.

## Websites
- **Tenor** works right away.
- **Giphy**, **Pexels** and **Pixabay** each need a free key. Click **Settings** in the app. Each site has a "get key" link; sign up, copy the key, paste it and press Save.
- Pexels and Pixabay are mostly real video, so pick "Real people" or "Both" with them.

Clips with words on them (memes, captions) are skipped automatically.

## Getting the .exe
Every change to this folder is built into a Windows .exe on GitHub and tested there by making a short real video. On GitHub, go to **Actions**, then **Build Clip Maker (Windows)**, open the latest green run, and download **ClipMaker-Windows** (or **ClipMaker-Windows-NVIDIA**) at the bottom.

## Running from source (any computer)
```
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
python app.py
```
