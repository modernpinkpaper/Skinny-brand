"""Clip Maker - paste a script, get a finished TikTok video (clips + voice + typed captions).
Runs a small web page on this computer only (127.0.0.1) and opens it in your browser.
Run from source:  python app.py      Self-test (used by the Windows build):  python app.py --selftest"""
import os, sys, json, re, socket, threading, traceback, webbrowser
from flask import Flask, request, jsonify, send_file, abort
from clipmaker.paths import PROJECTS, CACHE, SETTINGS, VOICES, device, device_name
from clipmaker.sources import SOURCES
from clipmaker.looks import LOOKS
from clipmaker import library

app = Flask(__name__)
STATE = dict(busy=False, stage="", pct=0, msg="", error="", project=None, video=None)
CANCEL = threading.Event()


class Cancelled(Exception): pass


def check_cancel():
    if CANCEL.is_set(): raise Cancelled()


def progress(pct, msg):
    check_cancel(); STATE.update(pct=round(float(pct), 1), msg=msg); print(f"[{STATE['pct']:5.1f}%] {msg}", flush=True)


def settings():
    try: return json.load(open(SETTINGS))
    except Exception: return {"keys": {}}


def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "video"


def project_dir(name): return os.path.join(PROJECTS, slug(name))


def load_project(name): return json.load(open(os.path.join(project_dir(name), "project.json"), encoding="utf-8"))


def save_project(p):
    os.makedirs(project_dir(p["name"]), exist_ok=True)
    json.dump(p, open(os.path.join(project_dir(p["name"]), "project.json"), "w", encoding="utf-8"), indent=1)


def background(stage, fn):
    if STATE["busy"]: return jsonify(error="Already working on something - wait or press Cancel."), 409
    CANCEL.clear(); STATE.update(busy=True, stage=stage, pct=0, msg="starting", error="")
    def run():
        try: fn()
        except Cancelled: STATE.update(error="Cancelled.")
        except Exception as e:
            traceback.print_exc(); STATE.update(error=str(e) or e.__class__.__name__)
        finally: STATE.update(busy=False)
    threading.Thread(target=run, daemon=True).start()
    return jsonify(ok=True)


@app.get("/")
def index(): return PAGE


@app.get("/api/options")
def options():
    return jsonify(sources=[dict(id=k, name=v[0], needs_key=v[2], key_url=v[3]) for k, v in SOURCES.items()],
                   looks=[dict(id=k, name=v["label"]) for k, v in LOOKS.items()],
                   voices=[dict(id=k, name=v[0]) for k, v in VOICES.items()],
                   settings=settings(), device=device(), projects=sorted(os.listdir(PROJECTS)), library=library.info())


@app.post("/api/settings")
def save_settings():
    s = settings(); s["keys"] = {k: v.strip() for k, v in request.json.get("keys", {}).items()}
    json.dump(s, open(SETTINGS, "w")); return jsonify(ok=True)


@app.post("/api/make")
def make():
    """One button: find the clips, then build the video right away (no checking step)."""
    from clipmaker import picker, render, direct
    o = request.json
    lines, breaks, dirs = direct.parse(o.get("script", ""))   # voice marks: [sad, slow], *word*, (pause)
    if not lines: return jsonify(error="Paste a script first."), 400
    if not o.get("sources"): return jsonify(error="Tick at least one website."), 400
    keys = settings().get("keys", {})
    missing = [SOURCES[s][0] for s in o["sources"] if SOURCES[s][2] and not keys.get(s)]
    if missing: return jsonify(error="Add a key in Settings for: " + ", ".join(missing)), 400
    name = slug(o.get("name") or lines[0][:30])
    def job():
        STATE.update(video=None, project=name)
        # the voice doesn't need the clips, so it is made at the same time as the clip search
        ref, end = VOICES[o.get("voice", "guy")][1], o.get("end", "")
        vstate = dict(msg="waiting", result=None, error=None)
        def voice_job():
            try:
                vstate["result"] = render.make_voice(lines, breaks, end, ref, float(o.get("speed", 0.92)),
                                                     lambda p, m: (check_cancel(), vstate.update(msg=m)), dirs)
                vstate["msg"] = "voice ready"
            except Exception as e:
                vstate["error"] = e
        progress(1, "loading")
        # load the big libraries once here: two threads importing them at the same time breaks the import
        import torch, torchaudio, transformers, chatterbox.tts, faster_whisper, noisereduce, rapidocr_onnxruntime  # noqa
        vt = threading.Thread(target=voice_job, daemon=True); vt.start()
        cands = picker.find_clips(lines, o["sources"], keys, o["kind"], o["look"],
                                  lambda p, m: progress(p * 0.6, f"finding clips: {m}  |  {vstate['msg']}"),
                                  live=bool(o.get("live")))
        p = dict(name=name, script=o["script"], lines=lines, breaks=breaks, opts=o, cands=cands, cur=[0] * len(lines))
        save_project(p)
        while vt.is_alive():
            progress(60, "clips found, finishing the voice: " + vstate["msg"]); vt.join(2)
        if vstate["error"]: raise vstate["error"]
        v = render.build(project_dir(name), name, lines, breaks, cands, end, o["look"], ref,
                         o.get("tags", ""), lambda p, m: progress(60 + p * 0.4, m), check_cancel,
                         audio_parts=vstate["result"], dirs=dirs)
        STATE.update(video=v, pct=100, msg="your video is ready")
    return background("make", job)


@app.post("/api/cancel")
def cancel(): CANCEL.set(); return jsonify(ok=True)


@app.get("/api/status")
def status(): return jsonify(STATE)


@app.post("/api/open")
def open_folder():
    d = project_dir(request.json["name"])
    if os.name == "nt": os.startfile(d)
    return jsonify(ok=True, folder=d)


@app.get("/media")
def media():
    f = os.path.abspath(request.args.get("f", ""))
    if not any(f.startswith(os.path.abspath(r) + os.sep) for r in (CACHE, PROJECTS)) or not os.path.exists(f): abort(404)
    return send_file(f, conditional=True)


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Clip Maker</title><style>
:root{--bg:#121214;--card:#1c1c20;--line:#2c2c33;--text:#ececf1;--dim:#9a9aa6;--acc:#c9a7ff;--bad:#ff8a8a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,Segoe UI,sans-serif}
main{max-width:1000px;margin:0 auto;padding:20px 16px 60px}h1{font-size:22px;margin:4px 0 16px}h2{font-size:16px;margin:0 0 10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px}
textarea{width:100%;min-height:260px;background:#0e0e10;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:10px;font:14px/1.5 inherit}
input[type=text],select{width:100%;background:#0e0e10;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}label{display:block;margin:3px 0}
.hint{color:var(--dim);font-size:13px}button{background:var(--acc);color:#1a1022;border:0;border-radius:8px;padding:10px 16px;font-weight:600;cursor:pointer}
button.ghost{background:transparent;color:var(--acc);border:1px solid var(--acc)}button:disabled{opacity:.5;cursor:default}
.bar{height:10px;background:#0e0e10;border-radius:6px;overflow:hidden;margin:8px 0}.bar i{display:block;height:100%;background:var(--acc);width:0}
.rows{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.row{background:#0e0e10;border:1px solid var(--line);border-radius:10px;overflow:hidden}.row video{width:100%;aspect-ratio:4/3;object-fit:cover;background:#000;display:block}
.row p{margin:8px;font-size:13px;min-height:38px}.row .b{display:flex;justify-content:space-between;align-items:center;padding:0 8px 8px}
.err{color:var(--bad)}.hide{display:none}.top{display:flex;justify-content:space-between;align-items:center}
</style></head><body><main>
<div class="top"><h1>Clip Maker</h1><button class="ghost" onclick="toggle('settings')">Settings</button></div>
<div id="settings" class="card hide"><h2>Website keys</h2><p class="hint">Tenor needs no key. The others give a free key after signing up on their site.</p><div id="keys"></div>
<button onclick="saveKeys()">Save</button></div>

<div class="card"><h2>1. Script</h2><p class="hint">One line = one clip. A blank line = a short pause. Two or more blank lines = a longer pause.</p>
<textarea id="script" placeholder="Paste your script here"></textarea>
<div class="grid" style="margin-top:12px">
 <div><b>Websites</b><div id="sources"></div>
  <label><input type="checkbox" id="live"> Also search live <span class="hint">(slower, finds newer clips)</span></label>
  <div class="hint" id="libinfo"></div></div>
 <div><b>Type of clips</b>
  <label><input type="radio" name="kind" value="animated" checked> Animated / cartoon</label>
  <label><input type="radio" name="kind" value="real"> Real people</label>
  <label><input type="radio" name="kind" value="both"> Both</label></div>
 <div><b>Look / colouring</b><select id="look"></select><br><br><b>Voice</b><select id="voice"></select>
  <br><br><b>Voice speed</b><select id="speed"><option value="1.0">Normal</option><option value="0.92" selected>A bit slower</option><option value="0.85">Slower</option></select></div>
 <div><b>Video name</b><input type="text" id="name" placeholder="e.g. absent-parent"><br><br>
  <b>End screen line</b><input type="text" id="end" value="send this to someone who needs to hear it"></div>
 <div><b>Hashtags</b><input type="text" id="tags" value="#healing #selflove #relatable #fyp"></div>
</div><br><button id="findBtn" onclick="make()">Make video</button> <span class="hint">It finds the clips and builds the video in one go. Clips with words on them are skipped.</span></div>

<div id="prog" class="card hide"><h2 id="stage">Working…</h2><div class="bar"><i id="barFill"></i></div>
<div id="msg" class="hint"></div><div id="err" class="err"></div><br><button class="ghost" onclick="post('/api/cancel',{})">Cancel</button></div>

<div id="done" class="card hide"><h2>2. Your video</h2><video id="final" controls style="max-height:70vh;max-width:100%"></video><br><br>
<button onclick="post('/api/open',{name:PROJECT})">Open folder</button> <span class="hint" id="where"></span></div>
</main><script>
let PROJECT=null,OPT=null,poll=null;
const $=id=>document.getElementById(id), toggle=id=>$(id).classList.toggle('hide');
const media=f=>'/media?f='+encodeURIComponent(f);
async function post(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});const j=await r.json();if(j.error)alert(j.error);return j}
async function init(){OPT=await (await fetch('/api/options')).json();
 $('sources').innerHTML=OPT.sources.map(s=>`<label><input type="checkbox" value="${s.id}" ${s.id=='tenor'?'checked':''}> ${s.name}${s.needs_key&&!OPT.settings.keys?.[s.id]?' <span class="hint">(needs key)</span>':''}</label>`).join('');
 $('libinfo').textContent=OPT.library?`Clip library: ${OPT.library.clips.toLocaleString()} ready-checked clips (${OPT.library.built})`:'Clip library: downloading… (until then it searches live)';
 $('look').innerHTML=OPT.looks.map(l=>`<option value="${l.id}">${l.name}</option>`).join('');
 $('voice').innerHTML=OPT.voices.map(v=>`<option value="${v.id}">${v.name}</option>`).join('');
 $('keys').innerHTML=OPT.sources.filter(s=>s.needs_key).map(s=>`<label>${s.name} <a href="${s.key_url}" target="_blank" style="color:var(--acc)">get key</a><input type="text" id="key_${s.id}" value="${OPT.settings.keys?.[s.id]||''}"></label>`).join('');
 const st=await (await fetch('/api/status')).json(); if(st.busy)watch();}
async function saveKeys(){const keys={};OPT.sources.filter(s=>s.needs_key).forEach(s=>keys[s.id]=$('key_'+s.id).value);await post('/api/settings',{keys});init();toggle('settings')}
async function make(){const b={script:$('script').value,name:$('name').value,end:$('end').value,tags:$('tags').value,look:$('look').value,voice:$('voice').value,speed:$('speed').value,live:$('live').checked,
 kind:document.querySelector('input[name=kind]:checked').value,sources:[...document.querySelectorAll('#sources input:checked')].map(x=>x.value)};
 const j=await post('/api/make',b); if(j.ok){$('done').classList.add('hide');watch()}}
function watch(){$('prog').classList.remove('hide');$('findBtn').disabled=true;clearInterval(poll);poll=setInterval(async()=>{
 const s=await (await fetch('/api/status')).json(); $('stage').textContent='Making your video… (about 20-30 min on a normal PC)';
 $('barFill').style.width=s.pct+'%'; $('msg').textContent=s.msg; $('err').textContent=s.error||'';
 if(!s.busy){clearInterval(poll);$('findBtn').disabled=false;
  if(!s.error&&s.video){$('prog').classList.add('hide');PROJECT=s.project;$('done').classList.remove('hide');
   $('final').src=media(s.video)+'&t='+Date.now();$('where').textContent=s.video}}},1000)}
init();
</script></body></html>"""


def selftest():
    """Makes a tiny real video through the app's own Make video button; used to test the Windows .exe."""
    import time
    library.update()
    c = app.test_client()
    r = c.post("/api/make", json=dict(script="Sometimes the quiet nights\nare where you heal the most.\n", name="selftest",
                                      sources=["tenor"], kind="animated", look="moody", voice="guy", end="", tags=""))
    assert r.status_code == 200, r.json
    t = time.time()
    while STATE["busy"]: time.sleep(2)
    v = STATE.get("video")
    ok = bool(v) and os.path.getsize(v) > 50000 and not STATE["error"]
    print("Using:", device_name(), flush=True)
    print("SELFTEST", "OK" if ok else "FAILED", v, STATE["error"], f"{time.time() - t:.0f}s", flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    url = f"http://127.0.0.1:{port}"
    print(f"\n  Clip Maker is running: {url}\n  Keep this window open while you use it. Close it to quit.\n"
          f"  Videos are saved in: {PROJECTS}\n  Using: {device_name()}\n", flush=True)
    threading.Thread(target=library.update, daemon=True).start()   # get / refresh the clip library
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, threaded=True)
