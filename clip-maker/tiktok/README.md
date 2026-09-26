# Finished videos → your TikTok drafts, 3 a day

Every morning at about 8 am (New York time), GitHub sends your next 3 finished videos to your **TikTok drafts**, oldest first. It never sends the same video twice. You then open TikTok whenever you like, paste the caption and press Post.

- **Captions:** TikTok doesn't let tools fill in a draft's caption. So every morning the Releases page **"Today's TikTok drafts"** shows the 3 captions, ready to copy.
- **How many a day:** change `per_day` in `clip-maker/tiktok/settings`.
- **Pages to never send:** add them to `skip` in the same file. For example, the test page `first-test` is skipped.
- **Send some right now:** Actions → **TikTok drafts** → Run workflow → action `send`.

## One-time setup (about 20 minutes)

### 1. Make a TikTok developer app
1. Go to **developers.tiktok.com** and log in with the TikTok account you post from. Then **Manage apps → Connect an app** (or Create app).
2. Fill in the basics: an app name (for example "Clip Maker"), an icon, a short description, and a category.
3. Under **Products**, add **Login Kit** and **Content Posting API**.
4. Under **Scopes**, make sure **user.info.basic** and **video.upload** are on.
5. In the **Login Kit** settings, add this **Redirect URI**, exactly:
   `https://github.com/modernpinkpaper/Skinny-brand`
6. Open the **Sandbox** tab, create a sandbox, and add your own TikTok account as a **Target user**. The sandbox lets your own account use the app without TikTok reviewing it. If TikTok says `video.upload` still needs a review, submit the app for review with a short note: "Personal tool that sends my own videos to my TikTok drafts; I publish them myself."
7. Copy the app's **Client key** and **Client secret**. Use the sandbox ones if you use the sandbox.

### 2. Add 3 GitHub secrets
In this repo: **Settings → Secrets and variables → Actions → New repository secret**:
- `TIKTOK_CLIENT_KEY`: the client key
- `TIKTOK_CLIENT_SECRET`: the client secret
- `TIKTOK_STORE_KEY`: the key Claude gave you. It locks your TikTok login so nobody can read it in this public repo.

### 3. Connect your TikTok account
1. Actions → **TikTok drafts** → Run workflow → action **link** → Run. Open the finished run and copy the long login link it printed.
2. Open that link, log in to TikTok and press **Authorize**. You land on this repo's GitHub page.
3. Copy the **whole address** from the address bar. It contains `code=...`.
4. Actions → **TikTok drafts** → Run workflow → action **connect**, paste the address in the code box → Run. It says "Connected to TikTok".

Done. The next morning, 3 videos arrive in your drafts. To test right away, run it with action **send**.

The connection lasts a year. If it ever stops, repeat step 3.
