"""Context: what are people actually watching for this trend on TikTok? Takes the topic as a hashtag, reads the most
viewed public posts (trends/tiktok_posts.py: captions + TikTok's own transcripts, no login), and counts the hashtags
used alongside it (for the caption). Research only: the script writer must never copy it.

  python trends/context.py robot          adds the context to today's trends/YYYY-MM-DD.json
"""
import os, re, sys, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import collector, tiktok_posts


def related_tags(posts, topic, n=8):
    skip = {"#fyp", "#foryou", "#foryoupage", "#viral", "#fypシ", "#trending", "#tiktok"}
    c = collections.Counter(t.lower() for p in posts for t in re.findall(r"#\w+", p["caption"]))
    return [t for t, _ in c.most_common(40) if t not in skip and not re.match(r"#fyp+", t)][:n]


def get(topic, n=8):
    tag = topic if topic.startswith("#") else collector.hashtag(topic)
    posts = tiktok_posts.top_posts(tag, n)
    return dict(hashtag=tag, posts=posts, related_hashtags=related_tags(posts, tag))


def path_for(topic):
    d = os.path.join(HERE, "research"); os.makedirs(d, exist_ok=True)   # git-ignored: other people's words stay off GitHub
    return os.path.join(d, f"{collector.today()}-{re.sub(r'[^a-z0-9]+', '-', topic.lower()).strip('-')}.json")


if __name__ == "__main__":
    topic = sys.argv[1]; c = get(topic)
    json.dump(c, open(path_for(topic), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(c["hashtag"], c["related_hashtags"], len(c["posts"]), "posts,", sum(bool(p["transcript"]) for p in c["posts"]), "with transcripts")
