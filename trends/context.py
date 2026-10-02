"""Context: what is the trend actually about? Reads the news stories behind a trend (headlines + the start of each
article) so the script writer understands it before writing. This is background only; the writer must not copy it.

  python trends/context.py "robot"      adds the context to today's trends/YYYY-MM-DD.json
"""
import os, re, sys, json, html, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def article_text(url, limit=1800):
    """The first paragraphs of a news page. Best effort: pages that refuse us (403) or are empty are skipped."""
    try:
        h = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=20).read().decode("utf8", "ignore")
    except Exception:
        return ""
    paras = (html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<p[^>]*>(.*?)</p>", h, re.S))
    real = lambda p: len(p.split()) >= 8 and p[-1] in ".!?\"”" and "{" not in p and len(p) / len(p.split()) < 9
    return " ".join(p for p in paras if real(p))[:limit]   # real sentences only, no menus or page code


def get(trend):
    """trend = one entry from the collector. Returns dict(headlines, excerpts)."""
    news = trend.get("news") or []
    return dict(headlines=[n["title"] if isinstance(n, dict) else n for n in news],
                excerpts=[dict(source=n.get("source", ""), text=t) for n in news if isinstance(n, dict)
                          for t in [article_text(n.get("url", ""))] if t])


if __name__ == "__main__":
    from datetime import date
    sys.path.insert(0, HERE); import collector
    path = os.path.join(HERE, f"{collector.today()}.json"); data = json.load(open(path, encoding="utf-8"))
    want = sys.argv[1].lower()
    trend = next(t for t in data["trends"] if t["topic"].lower() == want and t.get("news"))
    data.setdefault("context", {})[trend["topic"]] = get(trend)
    json.dump(data, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(data["context"][trend["topic"]], indent=1)[:1500])
