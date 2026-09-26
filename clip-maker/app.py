"""Clip Maker - paste a script, get a finished TikTok video (clips + voice + typed captions).
Runs a small web page on this computer only (127.0.0.1) and opens it in your browser.
Run from source:  python app.py      Self-test (used by the Windows build):  python app.py --selftest"""
import os, sys, json, re, socket, threading, traceback, webbrowser
from flask import Flask, request, jsonify, send_file, abort
from clipmaker.paths import PROJECTS, CACHE, SETTINGS, VOICES, device, device_name
from clipmaker.sources import SOURCES
from clipmaker.looks import LOOKS

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
                   settings=settings(), device=device(), projects=sorted(os.listdir(PROJECTS)))


@app.post("/api/settings")
def save_settings():
    s = settings(); s["keys"] = {k: v.strip() for k, v in request.json.get("keys", {}).items()}
    json.dump(s, open(SETTINGS, "w")); return jsonify(ok=True)


@app.post("/api/find")
def find():
    from clipmaker import picker
    o = request.json
    lines, breaks = picker.parse_script(o.get("script", ""))
    if not lines: return jsonify(error="Paste a script first."), 400
    if not o.get("sources"): return jsonify(error="Tick at least one website."), 400
    keys = settings().get("keys", {})
    missing = [SOURCES[s][0] for s in o["sources"] if SOURCES[s][2] and not keys.get(s)]
    if missing: return jsonify(error="Add a key in Settings for: " + ", ".join(missing)), 400
    name = o.get("name") or lines[0][:30]
    def job():
        cands = picker.find_clips(lines, o["sources"], keys, o["kind"], o["look"], progress)
        p = dict(name=slug(name), script=o["script"], lines=lines, breaks=breaks, opts=o, cands=cands,
                 cur=[0] * len(lines))
        save_project(p); STATE.update(project=p["name"], video=None, pct=100, msg="clips picked - check them below")
    return background("find", job)


@app.get("/api/project/<name>")
def project(name):
    p = load_project(name)
    rows = [dict(line=l, clip=c[k], n_alts=len(c)) for l, c, k in zip(p["lines"], p["cands"], p["cur"])]
    vid = os.path.join(project_dir(name), p["name"] + ".mp4")
    return jsonify(name=p["name"], rows=rows, opts=p["opts"], video=vid if os.path.exists(vid) else None)


@app.post("/api/swap")
def swap():
    from clipmaker import picker
    o = request.json; p = load_project(o["name"]); i = o["line"]
    taken = {c[k]["full"] for n, (c, k) in enumerate(zip(p["cands"], p["cur"])) if n != i}
    p["cur"][i] = picker.next_clip(p["cands"][i], p["cur"][i], taken)
    save_project(p); return jsonify(clip=p["cands"][i][p["cur"][i]])


@app.post("/api/build")
def build():
    from clipmaker import render
    p = load_project(request.json["name"]); o = p["opts"]
    def job():
        v = render.build(project_dir(p["name"]), p["name"], p["lines"], p["breaks"],
                         [c[k] for c, k in zip(p["cands"], p["cur"])], o.get("end", ""), o["look"],
                         VOICES[o.get("voice", "guy")][1], o.get("tags", ""), progress, check_cancel)
        STATE.update(video=v, project=p["name"], msg="your video is ready")
    return background("build", job)


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

<div class="card"><h2>1. Script</h2><p class="hint">One line = one clip. Leave a blank line where the voice should pause.</p>
<textarea id="script" placeholder="Paste your script here"></textarea>
<div class="grid" style="margin-top:12px">
 <div><b>Websites</b><div id="sources"></div></div>
 <div><b>Type of clips</b>
  <label><input type="radio" name="kind" value="animated" checked> Animated / cartoon</label>
  <label><input type="radio" name="kind" value="real"> Real people</label>
  <label><input type="radio" name="kind" value="both"> Both</label></div>
 <div><b>Look / colouring</b><select id="look"></select><br><br><b>Voice</b><select id="voice"></select></div>
 <div><b>Video name</b><input type="text" id="name" placeholder="e.g. absent-parent"><br><br>
  <b>End screen line</b><input type="text" id="end" value="send this to someone who needs to hear it"></div>
 <div><b>Hashtags</b><input type="text" id="tags" value="#healing #selflove #relatable #fyp"></div>
</div><br><button id="findBtn" onclick="find()">Find clips</button> <span class="hint">Clips with words on them are skipped automatically.</span></div>

<div id="prog" class="card hide"><h2 id="stage">Working…</h2><div class="bar"><i id="barFill"></i></div>
<div id="msg" class="hint"></div><div id="err" class="err"></div><br><button class="ghost" onclick="post('/api/cancel',{})">Cancel</button></div>

<div id="review" class="card hide"><div class="top"><h2>2. Check the clips</h2><button id="buildBtn" onclick="build()">Build video</button></div>
<p class="hint">Don't like one? Press "Swap" for the next best clip for that line.</p><div id="rows" class="rows"></div></div>

<div id="done" class="card hide"><h2>3. Your video</h2><video id="final" controls style="max-height:70vh;max-width:100%"></video><br><br>
<button onclick="post('/api/open',{name:PROJECT})">Open folder</button> <span class="hint" id="where"></span></div>
</main><script>
let PROJECT=null,OPT=null,poll=null;
const $=id=>document.getElementById(id), toggle=id=>$(id).classList.toggle('hide');
const media=f=>'/media?f='+encodeURIComponent(f);
async function post(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});const j=await r.json();if(j.error)alert(j.error);return j}
async function init(){OPT=await (await fetch('/api/options')).json();
 $('sources').innerHTML=OPT.sources.map(s=>`<label><input type="checkbox" value="${s.id}" ${s.id=='tenor'?'checked':''}> ${s.name}${s.needs_key&&!OPT.settings.keys?.[s.id]?' <span class="hint">(needs key)</span>':''}</label>`).join('');
 $('look').innerHTML=OPT.looks.map(l=>`<option value="${l.id}">${l.name}</option>`).join('');
 $('voice').innerHTML=OPT.voices.map(v=>`<option value="${v.id}">${v.name}</option>`).join('');
 $('keys').innerHTML=OPT.sources.filter(s=>s.needs_key).map(s=>`<label>${s.name} <a href="${s.key_url}" target="_blank" style="color:var(--acc)">get key</a><input type="text" id="key_${s.id}" value="${OPT.settings.keys?.[s.id]||''}"></label>`).join('');
 const st=await (await fetch('/api/status')).json(); if(st.busy)watch();}
async function saveKeys(){const keys={};OPT.sources.filter(s=>s.needs_key).forEach(s=>keys[s.id]=$('key_'+s.id).value);await post('/api/settings',{keys});init();toggle('settings')}
async function find(){const b={script:$('script').value,name:$('name').value,end:$('end').value,tags:$('tags').value,look:$('look').value,voice:$('voice').value,
 kind:document.querySelector('input[name=kind]:checked').value,sources:[...document.querySelectorAll('#sources input:checked')].map(x=>x.value)};
 const j=await post('/api/find',b); if(j.ok){$('review').classList.add('hide');$('done').classList.add('hide');watch()}}
function watch(){$('prog').classList.remove('hide');$('findBtn').disabled=true;clearInterval(poll);poll=setInterval(async()=>{
 const s=await (await fetch('/api/status')).json(); $('stage').textContent=s.stage=='build'?'Building your video…':'Finding clips…';
 $('barFill').style.width=s.pct+'%'; $('msg').textContent=s.msg; $('err').textContent=s.error||'';
 if(!s.busy){clearInterval(poll);$('findBtn').disabled=false;$('buildBtn').disabled=false;if(!s.error){$('prog').classList.add('hide');
  if(s.project){PROJECT=s.project;await show()}}}},1000)}
async function show(){const p=await (await fetch('/api/project/'+PROJECT)).json();$('review').classList.remove('hide');
 $('rows').innerHTML=p.rows.map((r,i)=>`<div class="row"><video id="v${i}" src="${media(r.clip.file)}" autoplay loop muted playsinline></video><p>${i+1}. ${r.line.replace(/</g,'&lt;')}</p>
 <div class="b"><span class="hint">${r.clip.source}</span><button class="ghost" onclick="swap(${i})">Swap</button></div></div>`).join('');
 if(p.video){$('done').classList.remove('hide');$('final').src=media(p.video)+'&t='+Date.now();$('where').textContent=p.video}}
async function swap(i){const j=await post('/api/swap',{name:PROJECT,line:i});if(j.clip)$('v'+i).src=media(j.clip.file)}
async function build(){$('buildBtn').disabled=true;const j=await post('/api/build',{name:PROJECT});if(j.ok)watch();else $('buildBtn').disabled=false}
init();
</script></body></html>"""


def selftest():
    """Makes a tiny real video from start to finish; used to test the Windows .exe after it's built."""
    from clipmaker import picker, render
    lines, breaks = picker.parse_script("Sometimes the quiet nights\nare where you heal the most.\n")
    say = lambda p, m: print(f"[{p:5.1f}%] {m}", flush=True)
    cands = picker.find_clips(lines, ["tenor"], {}, "animated", "moody", say)
    d = os.path.join(PROJECTS, "selftest")
    v = render.build(d, "selftest", lines, breaks, [c[0] for c in cands], "", "moody", VOICES["guy"][1], "", say)
    ok = os.path.getsize(v) > 50000
    print("Using:", device_name(), flush=True)
    print("SELFTEST", "OK" if ok else "FAILED", v, flush=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest()
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    url = f"http://127.0.0.1:{port}"
    print(f"\n  Clip Maker is running: {url}\n  Keep this window open while you use it. Close it to quit.\n"
          f"  Videos are saved in: {PROJECTS}\n  Using: {device_name()}\n", flush=True)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, threaded=True)
