"""What the clip library covers. Every topic is searched on Tenor as-is (mostly real TV / movie / talk show
clips) and with "anime" and "cartoon" added (animated). Add topics here and re-run the library build."""

EMOTIONS = """sad, crying, tears, heartbroken, lonely, alone, depressed, anxious, anxiety, overthinking, stressed,
angry, mad, frustrated, happy, laughing, smiling, excited, shocked, surprised, confused, tired, exhausted, bored,
nervous, scared, hopeful, peaceful, calm, relieved, proud, embarrassed, awkward, jealous, grateful, nostalgic, numb,
empty, hurt, betrayed, disappointed, regret, guilty, ashamed, insecure, confident, determined, motivated, in love,
blushing, crush, missing someone, longing, sorry, forgive, healing, broken, strong, brave, free, unbothered""".split(",")

ACTIONS = """walking away, walking alone, leaving, hugging, hug, holding hands, kiss, texting, phone, waiting,
running, dancing, eating, sleeping, lying in bed, staring out window, looking at sky, driving at night, sitting alone,
closing door, packing, looking in mirror, writing, reading, drinking coffee, cooking, cleaning, shopping, working,
studying, praying, screaming, sighing, thinking, daydreaming, remembering, waving goodbye, goodbye, hello,
celebrating, cheering, clapping, high five, fist bump, comforting, crying together, apologizing, arguing, fighting,
yelling, ignoring, rolling eyes, side eye, facepalm, shrug, nodding, shaking head no, thumbs up, slow clap,
sipping tea, judging, disgusted, smirk, wink, mind blown, wake up, get ready, glow up, working out, gym,
meditating, breathing, letting go, moving on, starting over""".split(",")

SETTINGS = """rain, rainy window, night city, city lights, train, train window, sunset, sunrise, ocean, beach,
waves, snow, forest, rooftop, bedroom, kitchen, school, classroom, office, car, bus stop, street at night, stars,
moon, sky, clouds, flowers, autumn, spring, summer, winter, candle, fireplace, cafe, library, park, bridge,
empty room, hallway, mirror""".split(",")

PEOPLE = """mom, dad, mother, father, parents, family, childhood, kid, baby, grandma, friends, best friend,
sisters, brothers, siblings, couple, boyfriend, girlfriend, husband, wife, ex, toxic relationship, red flag,
breakup, divorce, wedding, first date, teacher, boss, stranger, neighbor""".split(",")

LIFE = """self love, self care, confidence, success, money, rich, broke, bills, work, job, fired, new job,
graduation, birthday, party, holiday, christmas, vacation, travel, moving out, new home, pregnancy, new beginning,
second chance, time passing, years later, memories, flashback, old photos, growing up, getting older, life lesson,
advice, secret, lie, truth, trust, respect, loyalty, peace, silence, patience, karma, revenge, winning, losing,
failure, trying again, never give up""".split(",")

TOPICS = sorted({t.strip() for group in (EMOTIONS, ACTIONS, SETTINGS, PEOPLE, LIFE) for t in group if t.strip()})
STYLES = ["", " anime", " cartoon", " movie scene", " tv show", " aesthetic"]


def queries():
    """Every search the library build runs, in a fixed order (so shards split it the same way every time)."""
    return [t + s for t in TOPICS for s in STYLES]


if __name__ == "__main__":
    q = queries(); print(len(TOPICS), "topics,", len(q), "searches")
