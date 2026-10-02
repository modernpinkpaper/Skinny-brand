"""Brand filter: asks Claude (your ANTHROPIC_API_KEY) to score every trend for your brand and keep the best 3-5.
Skips tragedies, politics and real people's drama. Also suggests caption hashtags for each kept trend.
Reads trends/brand.md, so you can change what "fits" means by editing that file."""
import os, re, json
from typing import List
from pydantic import BaseModel

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "claude-sonnet-5"   # same writer model the rest of the repo uses (see clip-maker/tiktok_to_scripts.py)
KEEP = (3, 5)

RULES = """You choose which of today's trending topics are worth a TikTok voiceover video for my brand (profile above).

For EVERY trend in the list, give: fit (0-10), skip (true/false) and one plain-English line saying why it fits or
why not. Set skip=true (and fit=0) for anything about tragedies, deaths, disasters, violence, crime, politics or
politicians, elections, or real people's drama (feuds, breakups, scandals, lawsuits). Also skip sports scores and
product or game launches unless there is a clear, kind angle for my audience.

Topics tagged [niche] come with the recent most-viewed posts under them. For those, do not just return the hashtag:
read the posts and name the specific THEME people are responding to (e.g. "keeping an ex's door open is not loyalty"),
and use that as the topic. Several themes can come from one hashtag.

For the ones that fit, "angle" is the original idea for a video (one sentence, my own take: how the trend connects
to a feeling or habit my audience has). Never plan to copy another creator's script.
"hashtags" are 4-6 caption hashtags that suit the angle (lowercase, no spaces)."""


class Score(BaseModel):
    topic: str
    fit: int
    skip: bool
    why: str
    angle: str
    hashtags: List[str]

class Scores(BaseModel):
    scores: List[Score]


def niche_posts():
    """What the niche hashtags' recent top posts say (research only, kept out of GitHub)."""
    import collector
    p = os.path.join(HERE, "research", f"{collector.today()}-niche.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def pick(items, keep=KEEP):
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("No ANTHROPIC_API_KEY. Put it in the secrets (GitHub: Settings > Secrets and variables > Actions).")
    brand = open(os.path.join(HERE, "brand.md"), encoding="utf-8").read()
    names = list(dict.fromkeys(i["topic"] for i in items))
    user = "Today's trends:\n" + "\n".join(
        f"- {t}  [{', '.join(sorted({i['source'] for i in items if i['topic'] == t}))}]" for t in names)
    for tag, posts in niche_posts().items():
        user += f"\n\n[niche] #{tag} recent top posts:\n" + "\n".join(
            f"- ({p['views']:,} views) {p['caption'][:160]} | transcript: {p['transcript'][:350]}" for p in posts)
    r = anthropic.Anthropic(max_retries=8).messages.parse(
        model=MODEL, max_tokens=16000, output_format=Scores,
        system=[{"type": "text", "text": brand + "\n\n---\n\n" + RULES}],
        messages=[{"role": "user", "content": user}])
    ok = sorted((s for s in r.parsed_output.scores if not s.skip), key=lambda s: -s.fit)
    top = ok[:keep[1]]
    return dict(picked=[s.model_dump() for s in top], scored=[s.model_dump() for s in r.parsed_output.scores])
