#!/usr/bin/env python3
"""Let Python find its own comment categories (no AI/LLM): TF-IDF word weights + NMF topic modeling.
Words that keep showing up together become a "topic"; its top words become that topic's word list.
Usage: python3 tools/auto_topics.py comments.csv [number_of_topics]"""
import csv, random, re, sys, collections
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.decomposition import NMF

EXTRA_STOP = {"im", "ive", "id", "dont", "didnt", "cant", "wasnt", "got", "just", "like", "went", "did", "day", "year", "years",
              "time", "decided", "life", "changed", "change", "really", "know", "going", "way", "said", "told", "later", "ago",
              "lol", "yall", "u", "ur", "thing", "things", "today", "now", "one", "two", "first", "make", "made", "best", "ended",
              "started", "start", "want", "wanted", "every", "still", "never", "also", "back", "get", "go", "would", "could"}

def main():
    src = sys.argv[1]; k = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    rows, seen = [], set()
    for r in csv.DictReader(open(src, encoding="utf-8-sig")):
        if not r["reply_to"] and r["comment_id"] not in seen:
            seen.add(r["comment_id"]); rows.append(r)
    texts = [r["text"] for r in rows]
    vec = TfidfVectorizer(stop_words=list(ENGLISH_STOP_WORDS | EXTRA_STOP), ngram_range=(1, 2), min_df=4, max_df=0.3,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
    X = vec.fit_transform(texts)
    model = NMF(n_components=k, random_state=0, init="nndsvda", max_iter=500)
    W = model.fit_transform(X)
    words = vec.get_feature_names_out()
    topics = [[words[i] for i in comp.argsort()[::-1][:12]] for comp in model.components_]
    best = W.argmax(axis=1); strength = W.max(axis=1)
    cutoff = sorted(strength)[int(len(strength) * 0.35)]  # weakest 35% -> "Other"
    groups = collections.defaultdict(list)
    for i, r in enumerate(rows):
        groups[best[i] if strength[i] >= cutoff else -1].append(r)
    random.seed(3)
    for t in sorted(range(k), key=lambda t: -len(groups[t])):
        g = groups[t]
        print(f"\n### TOPIC {t+1}  ({len(g)} comments)")
        print("   word list:", ", ".join(topics[t]))
        for r in sorted(g, key=lambda r: -int(r["likes"]))[:3] + random.sample(g, min(3, len(g))):
            print("   -", r["text"][:110].replace("\n", " "))
    print(f"\n### OTHER (didn't clearly fit any topic): {len(groups[-1])} comments")

if __name__ == "__main__":
    main()
