"""Search Mixkit free stock videos. Usage: python3 mixkit_search.py "woman crying" [more queries...]"""
import re, sys, html, urllib.request, urllib.parse
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
def search(q):
    slug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")
    out = {}
    qs = urllib.parse.quote_plus(q)
    for url in (f"https://mixkit.co/search/?s={qs}&type=video", f"https://mixkit.co/free-stock-video/discover/{slug}/"):
        try:
            h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read().decode()
        except Exception:
            continue
        for m in re.finditer(r'data-item-grid--video-player-item-id-value="(\d+)".*?width="(\d+)" height="(\d+)".*?overlay-video-title">\s*(.*?)\s*</span>', h, re.S):
            vid, w, hh, title = m.groups()
            out[vid] = (html.unescape(title), "V" if int(hh) > int(w) else "H")
    return out
for q in sys.argv[1:]:
    res = search(q)
    print(f"## {q} ({len(res)})")
    for vid, (t, o) in list(res.items())[:14]:
        print(f"  {vid} [{o}] {t}")
