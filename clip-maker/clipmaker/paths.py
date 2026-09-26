"""Where things live. Works both from source and inside the PyInstaller .exe."""
import os, sys

FROZEN = getattr(sys, "frozen", False)
APP_DIR = sys._MEIPASS if FROZEN else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(APP_DIR, "assets")

# finished videos go to Documents\Clip Maker\<name>; downloads, cache and settings to AppData
PROJECTS = os.path.join(os.path.expanduser("~"), "Documents", "Clip Maker")
DATA = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share"), "ClipMaker")
CACHE = os.path.join(DATA, "cache")
SETTINGS = os.path.join(DATA, "settings.json")
for d in (PROJECTS, CACHE): os.makedirs(d, exist_ok=True)

VOICES = {"guy": ("Guy (warm, calm)", os.path.join(ASSETS, "voices", "guy.wav"))}


def device():
    """Uses an NVIDIA graphics card when there is one (much faster), otherwise the processor."""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def device_name():
    """What the black window shows, so you can see whether the NVIDIA card is being used."""
    try:
        import torch
        if torch.cuda.is_available(): return "NVIDIA graphics card: " + torch.cuda.get_device_name(0)
        if torch.version.cuda: return "processor only (this is the NVIDIA build, but no working NVIDIA card/driver was found)"
    except Exception:
        pass
    return "processor only (download the NVIDIA build to use an NVIDIA card)"
