# What They Said — entry writing guide

The book: a guided journal made from real answers to "What's something a family member said that you'll never fully forgive?" One story per page. Black & white print. Readers are mostly women 20–50 healing from family hurt.

Every entry has exactly 4 parts (this formula is approved — don't change it):

1. **story** — the person's own words, first person, lightly edited:
   - 18–60 words. Keep their voice and the exact hurtful line if there is one (in quotes).
   - Fix spelling/grammar and remove emojis, "lol", slang typos, but don't make it formal.
   - Anonymize: no names, places, schools, brands, dates, exact ages of kids; change tiny identifying details if needed. Ages like "I was 9" or "at 16" are fine.
   - Keep it gentle but honest. For sexual abuse use words like "abused" / "assaulted" (no graphic detail). For suicide, no methods.
   - If the BEST story is incomplete, you may merge in a detail from an "other" story in the same group — but keep it one person's believable story.
2. **shared_by** — "a daughter", "a son", "a sister", "a mother", "a granddaughter", "a niece", "a wife", "an adopted daughter", etc. Add an age range ("30s") only if the text makes their current age clear. Never invent.
3. **needed** — "What you needed to hear": 1–2 sentences (max ~35 words), spoken to them as "you". Name the lie they were told, then replace it with the truth. Warm, not preachy, no clichés ("you are enough", "everything happens for a reason"), no therapy jargon.
4. **prompt** — "Your turn": 2 parts, max ~35 words:
   - Part 1 — **find your version**: a question about the same hurt the story is about (stay close to the story).
   - Part 2 — **give yourself what was missing**: an action on the page (speak to your younger self, write what you deserved to hear, celebrate it here, write who you became, write a boundary, name the kind one, etc.).
   - Vary the Part 2 actions across entries so pages don't feel repetitive.

Approved examples (match this quality and tone):

- story: My brother died suddenly. At the funeral, my mother turned to me and said it should have been me instead — in front of my children.
  shared_by: a daughter, 30s
  needed: You were never the spare. Losing him doesn't make you worth less, and your grief counts too.
  prompt: Have you ever felt like the "less important" one? What would you say to the younger you who felt that way?
- story: I was crying, and my mom turned to my brother with a smile — "Isn't she so dramatic?" My brother was the one who came over and hugged me.
  shared_by: a sister, 20s
  needed: Your feelings were never "too much." The person who comforted you showed you what love is supposed to look like.
  prompt: Who was the kind one in your story? Write down one thing they did that you still remember.
- story: At my high school graduation, my dad leaned over and said, "Just because you accomplished something doesn't mean you're better than me." That was the last day we spoke.
  shared_by: a daughter, 20s
  needed: Your wins were never a threat to anyone who truly loved you. You were allowed to be proud of yourself that day — and you still are.
  prompt: What's something you accomplished that nobody celebrated with you? Celebrate it here, the way you deserved.
- story: They told me I'd be the first one pregnant and I'd never amount to anything. I own my home now, I was the last to have a baby, and I finish my master's next year.
  shared_by: a sister, 30s
  needed: Their words were a prediction, not a promise. You get to be the one who writes how your story goes.
  prompt: What did someone predict about you that turned out wrong? Write about who you became instead.

Also give each entry **strength** 1–5: how strong it is as a book page (clear, relatable, emotionally specific, not confusing, not too niche/odd). The editor will cut the weakest ~25 of 225 to reach 200.

Output: a JSON list (UTF-8, use Python json.dump with ensure_ascii=False, indent=1) of objects:
{"cid": <cluster number>, "story": "...", "shared_by": "...", "needed": "...", "prompt": "...", "strength": 1-5}
in the same order as the input file. One object per `=== cluster` block.
