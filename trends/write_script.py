"""Script step: gives a trend plus its background (trends/context.py) to YOUR script writer
(clip-maker/tiktok_to_scripts.py: FORMULA.md voice, length and style checks, one retry) and saves the script
as clip-maker/scripts/trend-<name>.txt, ready for the Make video workflow.

  python trends/write_script.py "robot"        (needs ANTHROPIC_API_KEY; picks the trend from today's file)
"""
import os, re, sys, json

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "clip-maker")); sys.path.insert(0, os.path.join(ROOT, "tools")); sys.path.insert(0, HERE)
import tiktok_to_scripts as w   # the existing writer: ask(), check(), clean_script(), guidance()

TREND_RULES = """

This script is about a trending topic. You get what is trending, what the most viewed TikTok posts about it show, and an angle.
- The posts are for understanding only. Never copy their words, and never copy another creator's script.
  Write it fresh, in my voice, from the angle of how this connects to the viewer's own life and feelings.
- Name no real person (no athletes, politicians, celebrities) and no drama about real people. Facts may be
  mentioned lightly, in plain words, only if they help the point. Never invent facts.
- Keep the topic itself short: the viewer should feel the script is about THEM within the first 5 lines."""


def build_prompt(trend, ctx, angle):
    posts = "\n\n".join(f"[{p['views']:,} views] caption: {p['caption'][:300]}" + (f"\ntranscript: {p['transcript'][:900]}" if p["transcript"] else "")
                         for p in ctx.get("posts", [])) or "(none)"
    return (f"Trending topic: {trend}\nMy angle for the video: {angle}\n\n"
            f"The most viewed TikTok posts on this topic right now (research only: what people watch, feel and worry about. "
            f"Do not copy any wording):\n{posts}")


def write(trend, ctx, angle, model=w.WRITERS["best"]):
    system = w.writer_system(w.guidance()) + TREND_RULES
    cost = []
    res = w.ask(system, build_prompt(trend, ctx, angle) + "\n\nOpen with hook template 2 or 12 from the formula.", w.Script, model, cost)
    if not res: raise SystemExit("Claude declined to write this one.")
    script, probs = w.clean_script(res.script), w.check(res.script)
    if probs:   # one retry with the problems spelled out, like the main writer does
        res2 = w.ask(system, build_prompt(trend, ctx, angle) + "\n\nYour first draft broke these rules:\n- " + "\n- ".join(probs) +
                     "\n\nFirst draft:\n" + res.script + "\n\nWrite the whole script again, fixed.", w.Script, model, cost)
        if res2 and len(w.check(res2.script)) < len(probs): script, probs = w.clean_script(res2.script), w.check(res2.script)
    return script, probs


def save(name, script, tags):
    path = os.path.join(ROOT, "clip-maker", "scripts", f"trend-{w.slug(name)}.txt")
    open(path, "w", encoding="utf-8").write(f"look: moody\nclips: animated\ntags: {tags}\n---\n{script}\n")
    return path


if __name__ == "__main__":
    import collector
    data = json.load(open(os.path.join(HERE, f"{collector.today()}.json"), encoding="utf-8"))
    topic = sys.argv[1]
    pick = next(p for p in data["picked"] if p["topic"].lower() == topic.lower())
    import context
    ctx = json.load(open(context.path_for(topic), encoding="utf-8")) if os.path.exists(context.path_for(topic)) else context.get(topic)
    pick["hashtags"] = list(dict.fromkeys(pick.get("hashtags", []) + ctx.get("related_hashtags", [])))
    script, probs = write(topic, ctx, pick.get("angle") or pick["why"])
    print("saved", save(topic, script, " ".join(pick.get("hashtags", []))), "| problems left:", probs or "none")
