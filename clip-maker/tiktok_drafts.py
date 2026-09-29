"""Sends finished videos to your TikTok drafts (inbox), a few each day, oldest first. Used by the
"TikTok drafts" workflow; you then open TikTok, paste the caption and press Post.

  python tiktok_drafts.py link              prints the TikTok login link (step 1 of connecting)
  python tiktok_drafts.py connect <code>    finishes connecting (paste the whole address you landed on)
  python tiktok_drafts.py send [N]          sends the next N videos (default: per_day in tiktok/settings)

Needs the repository secrets TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET and TIKTOK_STORE_KEY. The TikTok login is
kept encrypted in tiktok/login.enc (only TIKTOK_STORE_KEY can open it), so nothing readable is in the public repo."""
import os, sys, json, time, subprocess, tempfile, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(HERE, "tiktok")
LOGIN, SENT, SETTINGS = (os.path.join(DIR, f) for f in ("login.enc", "sent.txt", "settings"))
REDIRECT = "https://modernpinkpaper.com/pages/tiktok-connect"   # must match the Redirect URI in the TikTok app (a verified domain)
API = "https://open.tiktokapis.com/v2"
SINGLE_MAX, CHUNK = 64 * 1024 * 1024, 10 * 1024 * 1024


def settings():
    s = {"per_day": "3", "skip": ""}
    if os.path.exists(SETTINGS):
        for line in open(SETTINGS, encoding="utf-8"):
            if ":" in line and not line.strip().startswith("#"):
                k, v = [x.strip() for x in line.split(":", 1)]; s[k.lower()] = v
    return s


# ---------- the login, kept encrypted ----------
def _fernet():
    from cryptography.fernet import Fernet
    return Fernet(os.environ["TIKTOK_STORE_KEY"].encode())

def save_login(data):
    os.makedirs(DIR, exist_ok=True)
    open(LOGIN, "wb").write(_fernet().encrypt(json.dumps(data).encode()))

def load_login():
    if not os.path.exists(LOGIN): sys.exit("Not connected to TikTok yet: run the TikTok drafts workflow with 'connect' first.")
    return json.loads(_fernet().decrypt(open(LOGIN, "rb").read()))


def _post(url, data=None, token=None, form=False):
    headers = {"Content-Type": "application/x-www-form-urlencoded" if form else "application/json; charset=UTF-8"}
    if token: headers["Authorization"] = f"Bearer {token}"
    body = urllib.parse.urlencode(data).encode() if form else json.dumps(data or {}).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r: return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}") | {"_status": e.code}


def link():
    q = urllib.parse.urlencode({"client_key": os.environ["TIKTOK_CLIENT_KEY"], "scope": "user.info.basic,video.upload",
                                "response_type": "code", "redirect_uri": REDIRECT, "state": "clipmaker"})
    print("\nOpen this link, log in to TikTok and press Authorize:\n\n  https://www.tiktok.com/v2/auth/authorize/?" + q +
          "\n\nYou'll land on the TikTok Connected page on modernpinkpaper.com. Copy the WHOLE address from the address bar (it contains code=...)"
          "\nand run the TikTok drafts workflow again with action 'connect', pasting it in the code box.\n")


def connect(code):
    code = urllib.parse.parse_qs(urllib.parse.urlparse(code).query).get("code", [code])[0].strip()
    r = _post(f"{API}/oauth/token/", {"client_key": os.environ["TIKTOK_CLIENT_KEY"],
              "client_secret": os.environ["TIKTOK_CLIENT_SECRET"], "code": code, "grant_type": "authorization_code",
              "redirect_uri": REDIRECT}, form=True)
    if "refresh_token" not in r: sys.exit(f"TikTok did not accept the code: {r}")
    if "video.upload" not in r.get("scope", ""): sys.exit(f"Connected, but without video.upload permission (got: {r.get('scope')})")
    save_login({"refresh_token": r["refresh_token"], "open_id": r.get("open_id")})
    print("Connected to TikTok. Videos will now be sent to your drafts on schedule.")


def access_token():
    login = load_login()
    r = _post(f"{API}/oauth/token/", {"client_key": os.environ["TIKTOK_CLIENT_KEY"],
              "client_secret": os.environ["TIKTOK_CLIENT_SECRET"], "grant_type": "refresh_token",
              "refresh_token": login["refresh_token"]}, form=True)
    if "access_token" not in r:
        sys.exit(f"TikTok login expired or was removed - connect again. ({r})")
    if r.get("refresh_token") and r["refresh_token"] != login["refresh_token"]:   # TikTok may hand out a new one
        login["refresh_token"] = r["refresh_token"]; save_login(login)
    return r["access_token"]


# ---------- which videos ----------
def gh(*args):
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def queue(skip):
    """Every video on the "Videos: ..." release pages, oldest page first, in script order, not sent yet."""
    sent = set(open(SENT, encoding="utf-8").read().split()) if os.path.exists(SENT) else set()
    pages = json.loads(gh("release", "list", "--limit", "1000", "--json", "tagName,createdAt"))
    pages = sorted((p for p in pages if p["tagName"].startswith(("videos-", "video-"))), key=lambda p: p["createdAt"])
    out = []
    for p in pages:
        tag = p["tagName"]
        if any(s and s in tag for s in skip): continue
        assets = json.loads(gh("release", "view", tag, "--json", "assets"))["assets"]
        names = {a["name"] for a in assets}
        for a in sorted(assets, key=lambda a: a["name"]):
            if a["name"].endswith(".mp4") and f"{tag}/{a['name']}" not in sent:
                base = a["name"][:-4]
                cap = next((c for c in (f"{base}-caption.txt", "caption.txt") if c in names), None)
                out.append((tag, a["name"], cap))
    return out


def upload(token, path):
    size = os.path.getsize(path)
    if size <= SINGLE_MAX: chunk, count = size, 1
    else: chunk = CHUNK; count = size // chunk
    r = _post(f"{API}/post/publish/inbox/video/init/", {"source_info": {"source": "FILE_UPLOAD", "video_size": size,
              "chunk_size": chunk, "total_chunk_count": count}}, token)
    if r.get("error", {}).get("code") not in (None, "ok") or "data" not in r:
        raise RuntimeError(f"TikTok refused the upload: {r}")
    url, pid = r["data"]["upload_url"], r["data"]["publish_id"]
    with open(path, "rb") as f:
        for i in range(count):
            start = i * chunk
            end = size - 1 if i == count - 1 else start + chunk - 1   # the last chunk takes the rest
            f.seek(start); data = f.read(end - start + 1)
            req = urllib.request.Request(url, data=data, method="PUT", headers={
                "Content-Type": "video/mp4", "Content-Length": str(len(data)), "Content-Range": f"bytes {start}-{end}/{size}"})
            urllib.request.urlopen(req, timeout=600).read()
    for _ in range(30):   # wait until TikTok has it in the inbox
        time.sleep(10)
        st = _post(f"{API}/post/publish/status/fetch/", {"publish_id": pid}, token).get("data", {}).get("status", "")
        if st in ("SEND_TO_USER_INBOX", "PUBLISH_COMPLETE"): return pid
        if st == "FAILED": raise RuntimeError(f"TikTok could not process the video (publish_id {pid})")
    return pid


def send(n):
    s = settings()
    n = n or int(s["per_day"])
    todo = queue([x.strip() for x in s["skip"].split(",")])[:n]
    if not todo:
        print("No new videos to send.")
        try: gh("release", "edit", "tiktok-drafts-today", "--notes",
                f"# Today's TikTok drafts ({time.strftime('%A %B %d')})\n\nNo new videos today: every finished video has been sent.")
        except subprocess.CalledProcessError: pass
        return []
    token, done, tmp = access_token(), [], tempfile.mkdtemp()
    for tag, name, cap in todo:
        gh("release", "download", tag, "-p", name, "-D", tmp, "--clobber")
        caption = ""
        if cap:
            gh("release", "download", tag, "-p", cap, "-D", tmp, "--clobber")
            caption = open(os.path.join(tmp, cap), encoding="utf-8").read().strip()
        try:
            upload(token, os.path.join(tmp, name))
        except Exception as e:
            print(f"::error::{name}: {e}"); break
        open(SENT, "a", encoding="utf-8").write(f"{tag}/{name}\n")
        done.append((name, caption)); print(f"sent to your TikTok drafts: {name}", flush=True)
    left = len(queue([x.strip() for x in s["skip"].split(",")]))
    notes = [f"# Today's TikTok drafts ({time.strftime('%A %B %d')})\n",
             f"Open TikTok → Profile → Inbox/Drafts. {len(done)} new video(s) are waiting. Paste each caption, then Post.",
             f"{left} more videos are waiting to be sent on the next days.\n"]
    for i, (name, cap) in enumerate(done, 1):
        notes.append(f"## {i}. {name[:-4]}\n\n```\n{cap or '(no caption file)'}\n```\n")
    open(os.path.join(tmp, "notes.md"), "w", encoding="utf-8").write("\n".join(notes))
    try: gh("release", "view", "tiktok-drafts-today")
    except subprocess.CalledProcessError:
        gh("release", "create", "tiktok-drafts-today", "--title", "Today's TikTok drafts", "--notes", "starting", "--latest=false")
    gh("release", "edit", "tiktok-drafts-today", "--notes-file", os.path.join(tmp, "notes.md"))
    return done


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "send"
    if cmd == "link": link()
    elif cmd == "connect": connect(sys.argv[2])
    else: send(int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0)
