"""Writes the same topics with two (or more) writers, side by side, with the real cost of each.

  python compare_writers.py --csv ../research/post2-comments-all.csv --topics 4 --writers best,sonnet --out compare.md
  python compare_writers.py --link https://www.tiktok.com/... --topics 4

Uses the same topic picking and script writing as tiktok_to_scripts.py (FORMULA.md + PICKING.md)."""
import os, sys, csv, argparse
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiktok_to_scripts as T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv"); ap.add_argument("--link"); ap.add_argument("--topics", type=int, default=4)
    ap.add_argument("--writers", default="best,sonnet"); ap.add_argument("--out", default="compare.md")
    a = ap.parse_args()
    if a.csv: rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    else:
        sys.path.insert(0, os.path.join(os.path.dirname(T.HERE), "tools")); import tiktok_comments
        rows = tiktok_comments.scrape(a.link, replies=True, progress=lambda m: None)[1]
    comments = T.good_comments(rows); by_id = {c["id"]: c for c in comments}
    formula = T.guidance()
    writers = [w.strip() for w in a.writers.split(",") if w.strip() in T.WRITERS]
    ideas = T.plan(formula, comments[:T.CHUNK], a.topics, "", say=lambda m: print(m, flush=True))[:a.topics]
    plan_cost = T.spent["total"]

    def one(job):
        idea, w = job; cost = []
        hook = next((h for h in idea["hooks"] if 1 <= h <= 13), 1)
        script, probs = T.write_one(formula, idea, by_id, hook, T.WRITERS[w], cost)
        return idea["title"], w, hook, script, probs, sum(cost)
    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(one, [(i, w) for i in ideas for w in writers]))

    out = [f"# Writer comparison\n\n{len(rows)} comments, {len(comments)} read. Picking the {len(ideas)} topics "
           f"(always the best model) cost ${plan_cost:.2f}.\n"]
    totals = {w: [0.0, 0] for w in writers}
    for idea in ideas:
        out.append(f"\n---\n\n## {idea['title']}\n\n*{idea['kind']}.* On the surface: {idea['surface']}  \n"
                   f"Deeper need: {idea['deeper']}\n")
        for title, w, hook, script, probs, cost in results:
            if title != idea["title"]: continue
            totals[w][0] += cost; totals[w][1] += 1
            words = len((script or "").split())
            out.append(f"\n### {w} ({T.WRITERS[w]}) - hook {hook}, {words} words, ${cost:.3f}"
                       + (f", still off: {'; '.join(probs)}" if probs else "") + f"\n\n```\n{script or '(no script)'}\n```\n")
    out.append("\n---\n\n## Cost per script\n\n" + "\n".join(
        f"- **{w}**: ${t / max(n, 1):.3f} per script (about ${t / max(n, 1) * 300:.0f} for 300 videos)" for w, (t, n) in totals.items()))
    text = "\n".join(out)
    open(a.out, "w", encoding="utf-8").write(text)
    print("\n" + text, flush=True)


if __name__ == "__main__":
    main()
