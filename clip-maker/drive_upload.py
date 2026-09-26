"""Puts finished videos in a folder in your Google Drive. Used by the GitHub workflows.

  python drive_upload.py "<folder name>" file1.mp4 file1-caption.txt ...

Needs two GitHub secrets (see drive/README.md): GDRIVE_URL (your Apps Script web app link) and
GDRIVE_PASSWORD. Without them it does nothing. Files go in My Drive > Clip Maker Videos > <folder name>;
a file with the same name there is replaced, so making a video again doesn't leave duplicates."""
import os, sys, json, time
import urllib.request, urllib.parse

API = "https://www.googleapis.com/drive/v3/files"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"


def _req(url, data=None, headers=None, method=None):
    r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(r, timeout=300) as resp:
        return resp.status, dict(resp.headers), resp.read()


def get_pass(folder):
    """Asks your Apps Script for the folder id and a 1-hour upload pass."""
    body = json.dumps({"password": os.environ["GDRIVE_PASSWORD"], "folder": folder}).encode()
    for attempt in range(4):
        try:   # Apps Script answers with a redirect; urllib follows it with a GET, which is what it wants
            _, _, out = _req(os.environ["GDRIVE_URL"], body, {"Content-Type": "application/json"})
            res = json.loads(out)
            if "error" in res: sys.exit(f"Google Drive helper said: {res['error']}")
            return res["folderId"], res["token"]
        except (OSError, ValueError) as e:
            print(f"Drive helper not answering ({e}), retrying", flush=True); time.sleep(10 * (attempt + 1))
    sys.exit("Could not reach the Google Drive helper - check the GDRIVE_URL secret")


def upload(path, folder_id, token):
    name = os.path.basename(path)
    auth = {"Authorization": f"Bearer {token}"}
    q = f"name = '{name.replace(chr(39), chr(92) + chr(39))}' and '{folder_id}' in parents and trashed = false"
    _, _, out = _req(API + "?" + urllib.parse.urlencode({"q": q, "fields": "files(id)"}), headers=auth)
    old = json.loads(out).get("files", [])
    mime = "video/mp4" if name.endswith(".mp4") else "text/plain"
    if old:   # replace the file that's already there
        url, method, meta = f"{UPLOAD}/{old[0]['id']}?uploadType=resumable", "PATCH", {}
    else:
        url, method, meta = f"{UPLOAD}?uploadType=resumable", "POST", {"name": name, "parents": [folder_id]}
    _, h, _ = _req(url, json.dumps(meta).encode(), dict(auth, **{"Content-Type": "application/json; charset=UTF-8",
                                                                "X-Upload-Content-Type": mime}), method)
    loc = h.get("Location") or h.get("location")
    data = open(path, "rb").read()
    status, _, _ = _req(loc, data, {"Content-Type": mime, "Content-Length": str(len(data))}, "PUT")
    print(f"Google Drive: {'replaced' if old else 'added'} {name} ({status})", flush=True)


def main():
    if not (os.environ.get("GDRIVE_URL") and os.environ.get("GDRIVE_PASSWORD")):
        print("Google Drive not set up (no GDRIVE_URL / GDRIVE_PASSWORD secrets) - skipping"); return
    folder, files = sys.argv[1], [f for f in sys.argv[2:] if os.path.isfile(f)]
    if not files: return
    folder_id, token = get_pass(folder)
    for f in files:
        for attempt in range(3):
            try: upload(f, folder_id, token); break
            except OSError as e:
                print(f"upload of {f} failed ({e}), retrying", flush=True); time.sleep(15 * (attempt + 1))
        else:
            print(f"::warning::could not put {f} in Google Drive", flush=True)


if __name__ == "__main__":
    main()
