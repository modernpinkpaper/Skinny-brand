"""Popular posts for a hashtag, read from TikTok's PUBLIC hashtag page (tiktok.com/tag/<tag>) with headless Chromium.
No login and no account. For each post we keep: caption, views, likes, and the transcript when TikTok has made one
(its own auto captions, a public link, so no video is downloaded). Creator names are NOT kept.
Used only as research for your own original script."""
import os, re, sys

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def vtt_to_text(vtt):
    lines = [l.strip() for l in vtt.splitlines() if l.strip() and "-->" not in l and l.strip() != "WEBVTT" and not l.strip().isdigit()]
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def top_posts(tag, n=8, scrolls=2):
    """The n most-viewed posts that load on the hashtag page, each with its transcript if TikTok has one."""
    from playwright.sync_api import sync_playwright
    tag = tag.lstrip("#"); items = []
    with sync_playwright() as p:
        kw = dict(headless=True, args=["--no-sandbox"])
        if os.environ.get("HTTPS_PROXY"): kw["proxy"] = dict(server=os.environ["HTTPS_PROXY"])
        if os.environ.get("CHROMIUM_PATH"): kw["executable_path"] = os.environ["CHROMIUM_PATH"]
        b = p.chromium.launch(**kw)
        ctx = b.new_context(user_agent=UA, viewport=dict(width=1400, height=2000), locale="en-US"); pg = ctx.new_page()
        def on(r):
            if "challenge/item_list" in r.url:
                try: items.extend(r.json().get("itemList") or [])
                except Exception: pass
        pg.on("response", on)
        try:
            pg.goto(f"https://www.tiktok.com/tag/{tag}", wait_until="networkidle", timeout=60000); pg.wait_for_timeout(4000)
            for _ in range(scrolls): pg.mouse.wheel(0, 4000); pg.wait_for_timeout(2500)
        except Exception as e:
            print(f"  tiktok tag page failed: {str(e)[:100]}", file=sys.stderr)
        seen, posts = set(), []
        for it in sorted(items, key=lambda i: -int((i.get("stats") or {}).get("playCount") or 0)):
            if it["id"] in seen: continue
            seen.add(it["id"]); st = it.get("stats") or {}
            subs = [s for s in (it.get("video") or {}).get("subtitleInfos") or [] if str(s.get("LanguageCodeName", "")).startswith("eng")]
            text = ""
            if subs:
                try: text = vtt_to_text(ctx.request.get(subs[0]["Url"]).text())
                except Exception: pass
            posts.append(dict(caption=re.sub(r"\s+", " ", it.get("desc", "")).strip(), views=int(st.get("playCount") or 0),
                              likes=int(st.get("diggCount") or 0), seconds=(it.get("video") or {}).get("duration"), transcript=text))
            if len(posts) >= n: break
        b.close()
    return posts


if __name__ == "__main__":
    for p in top_posts(sys.argv[1]):
        print(f"{p['views']:>10,} views | {p['caption'][:80]!r}\n           transcript: {p['transcript'][:200]!r}")
