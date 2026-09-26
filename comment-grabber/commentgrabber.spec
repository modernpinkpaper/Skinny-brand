# PyInstaller recipe for CommentGrabber.exe (one file). Run: pyinstaller commentgrabber.spec
a = Analysis(["app.py"], pathex=[".", "../tools"], hiddenimports=["tiktok_comments", "comment_report"],
             excludes=["tkinter", "matplotlib", "numpy", "PIL", "pytest"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="CommentGrabber", console=True, icon=None)
