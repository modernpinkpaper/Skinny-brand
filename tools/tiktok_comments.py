#!/usr/bin/env python3
"""Scrape all comments (and replies) from a public TikTok post.
Usage: python3 tools/tiktok_comments.py <tiktok link> [out.csv] [--no-replies]"""
import csv, json, re, sys, time, urllib.request, datetime

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.tiktok.com/"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode()
                return json.loads(body) if body.strip() else {}
        except Exception:
            time.sleep(2 ** attempt)
    return {}

def resolve(link):
    req = urllib.request.Request(link, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        final = r.geturl()
    m = re.search(r"/(?:video|photo)/(\d+)", final)
    return final, m.group(1)

def rows_from(comments, parent=""):
    out = []
    for c in comments or []:
        u = c.get("user") or {}
        out.append({
            "comment_id": c.get("cid"), "reply_to": parent,
            "user": u.get("unique_id") or u.get("nickname"),
            "text": (c.get("text") or "").replace("\n", " "),
            "likes": c.get("digg_count", 0), "replies": c.get("reply_comment_total", 0),
            "date": datetime.datetime.utcfromtimestamp(c.get("create_time", 0)).strftime("%Y-%m-%d"),
            "liked_by_creator": c.get("is_author_digged", False),
        })
    return out

def main():
    link = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "comments.csv"
    want_replies = "--no-replies" not in sys.argv
    final, pid = resolve(link)
    print("post:", final.split("?")[0])
    rows, cursor, total = [], 0, None
    while True:
        d = get(f"https://www.tiktok.com/api/comment/list/?aid=1988&aweme_id={pid}&count=50&cursor={cursor}")
        total = total or d.get("total")
        batch = rows_from(d.get("comments"))
        rows += batch
        print(f"  top-level comments: {len([r for r in rows if not r['reply_to']])} / {total}", end="\r")
        if not d.get("has_more") or not batch:
            break
        cursor = d.get("cursor", cursor + 50)
        time.sleep(0.4)
    print()
    if want_replies:
        parents = [r for r in rows if not r["reply_to"] and r["replies"]]
        for i, p in enumerate(parents):
            rc = 0
            while True:
                d = get(f"https://www.tiktok.com/api/comment/list/reply/?aid=1988&item_id={pid}&comment_id={p['comment_id']}&count=50&cursor={rc}")
                batch = rows_from(d.get("comments"), parent=p["comment_id"])
                rows += batch
                if not d.get("has_more") or not batch:
                    break
                rc = d.get("cursor", rc + 50)
                time.sleep(0.3)
            print(f"  replies: fetched for {i+1}/{len(parents)} comments", end="\r")
        print()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    print(f"saved {len(rows)} comments to {out}")

if __name__ == "__main__":
    main()
