"""Comment Grabber - paste a TikTok link, get all its comments as a spreadsheet and a browse page.
Runs a small web page on this computer only (127.0.0.1) and opens it in your browser.
Run from source:  python app.py      Self-test (used by the Windows build):  python app.py --selftest"""
import os, sys, csv, json, re, socket, subprocess, threading, traceback, webbrowser, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
import tiktok_comments, comment_report

OUT = os.path.join(os.path.expanduser("~"), "Documents", "Comment Grabber")
os.makedirs(OUT, exist_ok=True)
STATE = dict(busy=False, msg="", error="", folder=None, summary=None)
CANCEL = threading.Event()
FILES = {  # file name -> what the page calls it
    "top-comments.csv": "Top comments (CSV)",
    "report.xlsx": "Excel report",
    "all-comments.csv": "All comments + replies (CSV)",
    "report.html": "Browse page",
}


class Cancelled(Exception): pass


def progress(msg):
    if CANCEL.is_set(): raise Cancelled()
    STATE["msg"] = msg; print(msg, flush=True)


def folder_name(post):
    m = re.search(r"@([^/]+)/(?:video|photo)/(\d+)", post)
    return f"{m.group(1)}-{m.group(2)}" if m else re.sub(r"\W+", "-", post)[-40:]


def grab(link, replies=True, limit=None):
    """Scrape one post and write the 4 files. Returns the folder name."""
    post, rows = tiktok_comments.scrape(link, replies=replies, limit=limit, progress=progress)
    if not rows: raise RuntimeError("No comments found. Is the post public, and does it have comments?")
    rows = list({r["comment_id"]: r for r in rows}.values())  # TikTok repeats some comments across pages
    name = folder_name(post); d = os.path.join(OUT, name); os.makedirs(d, exist_ok=True)
    progress("making the Excel report and browse page")
    tiktok_comments.save_csv(rows, os.path.join(d, "all-comments.csv"))
    tops = sorted([r for r in rows if not r["reply_to"]], key=lambda r: -int(r["likes"]))
    with open(os.path.join(d, "top-comments.csv"), "w", newline="", encoding="utf-8-sig") as f:  # -sig so Excel shows emojis
        w = csv.writer(f); w.writerow(["likes", "comment", "replies"])
        w.writerows([r["likes"], r["text"], r["replies"]] for r in tops)
    comment_report.build(rows, post, os.path.join(d, "report"))
    summary = dict(post=post, comments=len(tops), replies=len(rows) - len(tops))
    json.dump(summary, open(os.path.join(d, "info.json"), "w"))
    return name


def history():
    out = []
    for name in sorted(os.listdir(OUT), key=lambda n: -os.path.getmtime(os.path.join(OUT, n))):
        try: out.append(dict(folder=name, **json.load(open(os.path.join(OUT, name, "info.json")))))
        except Exception: pass
    return out


def start(link, replies):
    if STATE["busy"]: return "Already working on a post - wait or press Cancel."
    CANCEL.clear(); STATE.update(busy=True, msg="starting", error="", folder=None, summary=None)
    def run():
        try:
            name = grab(link, replies)
            STATE.update(folder=name, summary=json.load(open(os.path.join(OUT, name, "info.json"))))
        except Cancelled: STATE.update(error="Cancelled.")
        except Exception as e:
            traceback.print_exc(); STATE.update(error=str(e) or e.__class__.__name__)
        finally: STATE.update(busy=False)
    threading.Thread(target=run, daemon=True).start()


def open_folder(path):
    if sys.platform == "win32": os.startfile(path)
    else: subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def send(self, body, ctype="application/json", code=200, extra=None):
        if isinstance(body, (dict, list)): body = json.dumps(body)
        if isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", len(body))
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(body)

    def do_GET(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path)
        if path == "/": return self.send(PAGE, "text/html; charset=utf-8")
        if path == "/api/status": return self.send(STATE)
        if path == "/api/history": return self.send(dict(items=history(), files=FILES, out=OUT))
        m = re.fullmatch(r"/files/([^/]+)/([^/]+)", path)
        if m and m.group(2) in FILES and ".." not in m.group(1):
            f = os.path.join(OUT, m.group(1), m.group(2))
            if os.path.isfile(f):
                ctype = {"html": "text/html; charset=utf-8", "csv": "text/csv; charset=utf-8",
                         "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}[f.rsplit(".", 1)[1]]
                extra = {} if f.endswith(".html") else {"Content-Disposition": f'attachment; filename="{m.group(1)}-{m.group(2)}"'}
                return self.send(open(f, "rb").read(), ctype, extra=extra)
        self.send({"error": "not found"}, code=404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if self.path == "/api/grab":
            link = (body.get("link") or "").strip()
            if "tiktok.com" not in link: return self.send({"error": "Paste a TikTok link (it should have tiktok.com in it)."}, code=400)
            err = start(link, bool(body.get("replies", True)))
            return self.send({"error": err} if err else {"ok": True}, code=409 if err else 200)
        if self.path == "/api/cancel": CANCEL.set(); return self.send({"ok": True})
        if self.path == "/api/open":
            name = body.get("folder") or ""
            open_folder(os.path.join(OUT, name) if name and ".." not in name else OUT); return self.send({"ok": True})
        self.send({"error": "not found"}, code=404)


def free_port(start=8765):
    for p in range(start, start + 50):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)): return p
    return 0


def selftest():
    """Packaging check: make a report from a tiny sample, then try a small live grab (a TikTok block only warns)."""
    rows = [dict(comment_id="1", reply_to="", user="a", text="I started walking every day and lost 20 lbs", likes="50", replies="1", date="2026-01-01", liked_by_creator="False"),
            dict(comment_id="2", reply_to="1", user="b", text="how long did it take?", likes="3", replies="0", date="2026-01-02", liked_by_creator="False")]
    d = os.path.join(OUT, "selftest"); os.makedirs(d, exist_ok=True)
    comment_report.build(rows, "selftest", os.path.join(d, "report"))
    assert os.path.getsize(os.path.join(d, "report.xlsx")) > 1000 and os.path.getsize(os.path.join(d, "report.html")) > 1000
    print("offline report: OK")
    try:
        name = grab("https://www.tiktok.com/@jenandtonic/video/7549666097579216158", replies=True, limit=50)
        print("live grab: OK ->", os.path.join(OUT, name), json.load(open(os.path.join(OUT, name, "info.json"))))
    except Exception as e:
        print("WARNING: live grab failed (TikTok may block this computer):", e)


PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Comment Grabber</title><style>
:root{--bg:#FBF5EF;--card:#fff;--ink:#2B1E23;--muted:#7B6A70;--line:#EBDCD6;--hot:#C8325F;--soft:#FCEDEA}
@media (prefers-color-scheme:dark){:root{--bg:#1c1518;--card:#271e22;--ink:#f3e9ec;--muted:#b19fa5;--line:#3a2d32;--soft:#352529}}
*{box-sizing:border-box}[hidden]{display:none!important}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 60px}h1{font-size:24px;margin:0 0 4px}.sub{color:var(--muted);margin:0 0 18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:16px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
input[type=url]{flex:1;min-width:220px;padding:12px;border:1px solid var(--line);border-radius:10px;background:var(--bg);color:var(--ink);font-size:16px}
button,a.btn{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:10px;padding:10px 14px;font-size:15px;cursor:pointer;text-decoration:none;display:inline-block}
button.go{background:var(--hot);border-color:var(--hot);color:#fff;font-weight:600;padding:12px 20px}button:disabled{opacity:.5;cursor:default}
label{color:var(--muted);font-size:14px;display:flex;gap:6px;align-items:center;margin-top:10px}
#status{margin-top:12px;color:var(--muted);min-height:1.5em}#status.err{color:var(--hot);font-weight:600}
.done h2{font-size:18px;margin:0 0 4px}.done .sub{margin-bottom:12px;word-break:break-all}
iframe{width:100%;height:75vh;border:1px solid var(--line);border-radius:14px;background:var(--bg)}
.past{display:flex;justify-content:space-between;gap:10px;align-items:center;padding:8px 0;border-bottom:1px dashed var(--line)}.past:last-child{border:0}
.past span{word-break:break-all;font-size:14px}.past small{color:var(--muted)}
</style></head><body><main>
<h1>💬 Comment Grabber</h1><p class="sub">Paste a TikTok link. You get every comment as a spreadsheet and a page you can search.</p>
<div class="card"><div class="row"><input id="link" type="url" placeholder="https://www.tiktok.com/@name/video/123...  or  https://vm.tiktok.com/..."><button class="go" id="go">Get comments</button><button id="cancel" hidden>Cancel</button></div>
<label><input type="checkbox" id="replies" checked> Include replies (slower on big posts)</label><div id="status"></div></div>
<div id="result"></div>
<div class="card"><div class="row" style="justify-content:space-between"><b>Past grabs</b><button id="openall">Open folder</button></div><div id="history"></div></div>
</main><script>
const $=s=>document.querySelector(s);const esc=s=>String(s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let FILES={};
async function api(p,body){const r=await fetch(p,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});return r.json();}
function show(folder,s){
  $('#result').innerHTML=`<div class="card done"><h2>✅ ${s.comments.toLocaleString()} comments, ${s.replies.toLocaleString()} replies</h2><div class="sub">${esc(s.post)}</div>
  <div class="row">${Object.entries(FILES).map(([f,label])=>f.endsWith('.html')?`<a class="btn" target="_blank" href="/files/${encodeURIComponent(folder)}/${f}">${label} ↗</a>`:`<a class="btn" href="/files/${encodeURIComponent(folder)}/${f}">⬇ ${label}</a>`).join('')}
  <button data-open="${esc(folder)}">Open folder</button></div></div>
  <iframe src="/files/${encodeURIComponent(folder)}/report.html"></iframe>`;}
async function loadHistory(){const h=await api('/api/history');FILES=h.files;
  $('#history').innerHTML=h.items.length?h.items.map(i=>`<div class="past"><span>${esc(i.post)}<br><small>${i.comments.toLocaleString()} comments · ${i.replies.toLocaleString()} replies</small></span><button data-show="${esc(i.folder)}">View</button></div>`).join(''):'<p class="sub">Nothing yet.</p>';
  window.PAST=Object.fromEntries(h.items.map(i=>[i.folder,i]));}
function busy(b){$('#go').disabled=b;$('#cancel').hidden=!b;}
async function poll(){const s=await api('/api/status');const st=$('#status');
  st.className=s.error?'err':'';st.textContent=s.error||s.msg;
  if(s.busy){busy(true);setTimeout(poll,700);return;}
  busy(false);if(s.folder&&!s.error){st.textContent='Done. Saved in your Documents › Comment Grabber folder.';await loadHistory();show(s.folder,s.summary);}}
$('#go').onclick=async()=>{const link=$('#link').value.trim();if(!link){$('#link').focus();return;}
  $('#result').innerHTML='';const r=await api('/api/grab',{link,replies:$('#replies').checked});
  if(r.error){$('#status').className='err';$('#status').textContent=r.error;return;}poll();};
$('#link').addEventListener('keydown',e=>{if(e.key==='Enter')$('#go').click();});
$('#cancel').onclick=()=>api('/api/cancel',{});
$('#openall').onclick=()=>api('/api/open',{});
document.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
  if(b.dataset.show){show(b.dataset.show,PAST[b.dataset.show]);window.scrollTo({top:0,behavior:'smooth'});}
  if(b.dataset.open)api('/api/open',{folder:b.dataset.open});});
loadHistory().then(poll);
</script></body></html>"""

if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit(0)
    port = free_port()
    url = f"http://127.0.0.1:{port}/"
    print(f"Comment Grabber is running at {url}\nKeep this window open. Close it to stop.\nFiles are saved in {OUT}", flush=True)
    threading.Timer(1, lambda: webbrowser.open(url)).start()
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
