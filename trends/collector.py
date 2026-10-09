"""Trend collector: finds what is trending today, and saves it to trends/YYYY-MM-DD.json.

  python trends/collector.py                 collect + save (no AI, no videos)
  python trends/collector.py --pick          also score each trend for the brand (needs ANTHROPIC_API_KEY)

Sources (each trend is saved with its source and rank):
  google   Google Trends US daily trending searches (RSS feed)
  tiktok   TikTok Creative Center, public page, read with headless Chromium. NO login, no account.
           Logged out, TikTok shows only the top 3 hashtags per time window, so we read the 7-day and 30-day pages.
  niche    your niche hashtags in trends/niche_tags.txt (relationships, mental health...): recent posts getting the most views
  manual   trends/my_searches.txt, terms you paste from Creator Search Insights (one per line)
"""
import os, re, sys, json, datetime, urllib.request, xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
GOOGLE_RSS = "https://trends.google.com/trending/rss?geo=US"
TIKTOK_URL = "https://ads.tiktok.com/creative/creativeCenter/trends/hashtag?countryCode=US&period={p}&region=US"
TIKTOK_PERIODS = (7, 30)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def today():
    return datetime.datetime.now(ZoneInfo("America/New_York")).date().isoformat()


def from_google():
    req = urllib.request.Request(GOOGLE_RSS, headers={"User-Agent": UA})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for rank, it in enumerate(root.iter("item"), 1):
        news = [dict(title=n.findtext("ht:news_item_title", "", ns), url=n.findtext("ht:news_item_url", "", ns),
                     source=n.findtext("ht:news_item_source", "", ns)) for n in it.findall("ht:news_item", ns)]
        out.append(dict(source="google", rank=rank, topic=it.findtext("title", "").strip(),
                        traffic=it.findtext("ht:approx_traffic", "", ns), news=[n for n in news if n["title"]][:3]))
    return out


def from_tiktok():
    """Public Creative Center page. The list is built by JavaScript, so a headless browser reads it."""
    from playwright.sync_api import sync_playwright
    out = []
    with sync_playwright() as p:
        kw = dict(headless=True, args=["--no-sandbox"])
        if os.environ.get("HTTPS_PROXY"): kw["proxy"] = dict(server=os.environ["HTTPS_PROXY"])   # only the cloud sandbox has one
        if os.environ.get("CHROMIUM_PATH"): kw["executable_path"] = os.environ["CHROMIUM_PATH"]
        b = p.chromium.launch(**kw)
        ctx = b.new_context(user_agent=UA, viewport=dict(width=1400, height=2000), locale="en-US")
        for period in TIKTOK_PERIODS:
            pg = ctx.new_page()
            try:
                pg.goto(TIKTOK_URL.format(p=period), wait_until="networkidle", timeout=90000); pg.wait_for_timeout(4000)
                text = pg.inner_text("body")
            except Exception as e:
                print(f"  tiktok {period}-day page failed: {str(e)[:100]}", file=sys.stderr); continue
            finally:
                pg.close()
            # the list reads: rank / #tag / category (optional) / 60.3K / Posts / 613.3M / Views
            for m in re.finditer(r"\n(\d+)\n(#\w+)\n(?:([^\n#]+)\n)?([\d.,]+[KMB]?)\nPosts\n([\d.,]+[KMB]?)\nViews", text):
                out.append(dict(source=f"tiktok-{period}d", rank=int(m[1]), topic=m[2], category=(m[3] or "").strip(),
                                posts=m[4], views=m[5]))
        b.close()
    return out


def from_niche(days=14, per_tag=5):
    """Your niche hashtags (trends/niche_tags.txt): for each, the recent posts that are getting the most views.
    The posts themselves go to trends/research/ (git-ignored); the trend list only keeps the numbers."""
    import tiktok_posts
    path = os.path.join(HERE, "niche_tags.txt")
    tags = [l.strip().lstrip("#") for l in open(path, encoding="utf-8-sig")] if os.path.exists(path) else []
    out, research = [], {}
    for tag in [t for t in tags if t and not t.startswith("# ")]:
        posts = tiktok_posts.top_posts(tag, per_tag, 2, max_age_days=days)
        if not posts: continue
        research[tag] = posts
        out.append(dict(source="niche", topic="#" + tag, posts=len(posts), views=sum(p["views"] for p in posts), best=posts[0]["views"]))
    for rank, t in enumerate(sorted(out, key=lambda t: -t["views"]), 1): t["rank"] = rank
    os.makedirs(os.path.join(HERE, "research"), exist_ok=True)
    json.dump(research, open(os.path.join(HERE, "research", f"{today()}-niche.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return out


def from_manual():
    path = os.path.join(HERE, "my_searches.txt")
    if not os.path.exists(path): return []
    terms = [l.strip() for l in open(path, encoding="utf-8-sig") if l.strip() and not l.strip().startswith("# ") and l.strip() != "#"]
    terms = [t for t in terms if not t.startswith("# ")]
    return [dict(source="manual", rank=i, topic=t) for i, t in enumerate(terms, 1)]


def hashtag(term):
    """'why am i always tired' -> '#whyamialwaystired'; an existing #tag stays as it is."""
    w = re.sub(r"[^a-z0-9]", "", term.lower())
    return f"#{w}" if w and len(w) <= 30 else ""


def collect():
    items = []
    for name, fn in (("niche", from_niche), ("google", from_google), ("tiktok", from_tiktok), ("manual", from_manual)):
        try:
            got = fn(); print(f"  {name}: {len(got)} trends")
            items += got
        except Exception as e:
            print(f"  {name} FAILED: {str(e)[:150]}", file=sys.stderr)
    return items


def save(items, extra=None):
    day = today()
    path = os.path.join(HERE, f"{day}.json")
    data = dict(date=day, trends=items, **(extra or {}))
    json.dump(data, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    return path


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    items = collect()
    extra = None
    if "--pick" in sys.argv:
        import brand_filter
        extra = brand_filter.pick(items)
    print("saved", save(items, extra))
