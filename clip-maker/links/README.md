# TikTok link → lots of videos

Put a TikTok link here and GitHub does the rest:

1. It grabs every comment on the post.
2. Claude studies the comments and groups them into topics, following `clip-maker/PICKING.md`. For each topic it notes what's happening on the surface, the deeper pain or need, whether it's Emotional, Practical or Educational, and which of your formula's hook templates fit it. There's no limit on topics, and it never stops to ask.
3. Claude writes **3 scripts per topic**, each opening with a different hook from `clip-maker/FORMULA.md`, so one topic becomes 3 different videos. You can change the number with the `versions` setting. Each script is checked against the rules and sent back once if it breaks one.
4. **The moment each script is written, its video starts being made.** It doesn't wait for the other scripts. Up to 20 videos are made at the same time; the rest wait their turn, so it keeps going until every script has its video.
5. Each finished video lands on one Releases page, **Videos: <name>**, with its own caption file. If Google Drive is set up, it also goes to My Drive → Personal → TikTok Videos → <name>. See `../drive/README.md`.
6. At the end the scripts are also saved in `clip-maker/scripts/<name>/`, one file per video.

## One-time setup: your Claude API key
The key is kept in a GitHub **secret**, never in a file. This repo is public, so a key in a file could be read and used by anyone.

1. Get a key at console.anthropic.com → API keys.
2. In this repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
3. Name: `ANTHROPIC_API_KEY`. Secret: paste the key. Press **Add secret**.

To change the key later, open the same page, click the pencil next to `ANTHROPIC_API_KEY`, and paste the new one.

## Making videos from a link
1. In this folder, tap **Add file → Create new file**.
2. Name it after the batch, e.g. `family post`.
3. Paste the TikTok link. That's all you need. You can also add settings, one per line:

```
https://www.tiktok.com/@someone/video/1234567890
videos: 50
look: auto
clips: auto
speed: a bit slower
tags: #healing #family
notes: focus on the comments about mothers
```

| Setting | What it does |
|---|---|
| `videos` | The most videos to make in total. Leave it out (or write `all`) for every topic, up to 1,000. |
| `versions` | How many videos per topic, each with a different hook. Default 3. `1` gives one video per topic; up to 13. |
| `look` | `auto` lets Claude pick per video. Or: moody, vintage, bright, pastel, black and white. |
| `clips` | `auto` lets Claude pick per video. Or: animated, real, both. |
| `speed` | normal, a bit slower, slower |
| `end`, `tags` | Same as in a script file. |
| `notes` | Anything Claude should keep in mind when picking ideas. |

4. Tap **Commit changes**. Watch it in **Actions → TikTok to videos**.

## How many videos, how long, what it costs
- **How many:** 3 videos per topic (or your `versions` number). A post with a few thousand real comments can give hundreds. A post full of jokes or one-word comments gives very few. It never repeats a topic, so the count depends on the comments.
- **How long:**
  - The first video is ready about 20 minutes after you add the link.
  - After that, about 20 videos finish every 15 minutes. So 100 videos take about 1.5 hours, and 300 take about 4 hours.
- **Cost:**
  - GitHub: free, because this repo is public.
  - Claude: roughly 5 to 10 cents per script, plus about $1 for reading the comments. So about $5 to $10 for 100 scripts.

To edit a script afterwards, open it in `clip-maker/scripts/<name>/` and save it. That makes that one video again, on its own Releases page.
