# PyInstaller recipe for ClipMaker.exe (folder build). Run: pyinstaller clipmaker.spec
from PyInstaller.utils.hooks import collect_all, copy_metadata

datas, binaries, hidden = [("assets", "assets")], [], []
for pkg in ["chatterbox", "perth", "s3tokenizer", "rapidocr_onnxruntime", "faster_whisper", "ctranslate2",
            "onnxruntime", "librosa", "imageio_ffmpeg", "noisereduce", "conformer", "spacy_pkuseg", "pykakasi",
            "omegaconf", "diffusers", "transformers", "tokenizers", "safetensors", "soundfile", "audioread",
            "lazy_loader", "numba", "llvmlite", "pyloudnorm", "flask", "jinja2", "werkzeug"]:
    try:
        d, b, h = collect_all(pkg); datas += d; binaries += b; hidden += h
    except Exception as e:
        print("skip", pkg, e)
for pkg in ["torch", "torchaudio", "transformers", "tokenizers", "huggingface-hub", "safetensors", "tqdm", "regex",
            "requests", "packaging", "filelock", "numpy", "pyyaml", "diffusers", "accelerate", "librosa",
            "chatterbox-tts", "resemble-perth", "faster-whisper", "imageio-ffmpeg", "rapidocr-onnxruntime", "flask"]:
    try: datas += copy_metadata(pkg)
    except Exception as e: print("no metadata", pkg, e)

a = Analysis(["app.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=["gradio", "gradio_client", "matplotlib", "IPython", "tkinter", "pytest"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ClipMaker", console=True, icon=None)
coll = COLLECT(exe, a.binaries, a.datas, name="ClipMaker")
