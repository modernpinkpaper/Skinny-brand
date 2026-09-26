# TikTok link → lots of videos

Put a TikTok link here and GitHub does the rest:

1. It grabs every comment on the post.
2. Claude reads them and finds every different video idea in them. It skips jokes, spam and anything that doesn't fit your formula.
3. Claude writes one script per idea, following `clip-maker/FORMULA.md` (voice marks included). Each script is checked against the formula's rules and sent back once if it breaks one.
4. The scripts are saved in `clip-maker/scripts/<name>/`, one file per video.
5. All the videos are made, up to 20 at a time. They land on one Releases page called **Videos: <name>**, each with its own caption file.

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
| `videos` | The most videos to make. Leave it out (or write `all`) to make one for every good idea in the comments, up to 500. |
| `look` | `auto` lets Claude pick per video. Or: moody, vintage, bright, pastel, black and white. |
| `clips` | `auto` lets Claude pick per video. Or: animated, real, both. |
| `speed` | normal, a bit slower, slower |
| `end`, `tags` | Same as in a script file. |
| `notes` | Anything Claude should keep in mind when picking ideas. |

4. Tap **Commit changes**. Watch it in **Actions → TikTok to videos**.

## How many videos, how long, what it costs
- **How many:** one per different idea in the comments. A post with a few thousand real stories often gives 50 to 200 or more. A post full of jokes or one-word comments gives very few. It never makes the same idea twice, so the count depends on the comments.
- **How long:**
  - Scripts: about 30 minutes for 100.
  - Videos: about 15 minutes each, 20 at a time, so about 1.5 hours for 100 videos and about 4 hours for 300.
- **Cost:**
  - GitHub: free, because this repo is public.
  - Claude: roughly 5 to 10 cents per script, plus about $1 for reading the comments. So about $5 to $10 for 100 scripts.

To edit a script afterwards, open it in `clip-maker/scripts/<name>/` and save it. That makes that one video again, on its own Releases page.
