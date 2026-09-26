# Videos straight into your Google Drive

Once this is set up, every finished video, and its caption file, also goes into your Google Drive:
- **Videos from a TikTok link:** My Drive → Personal → **TikTok Videos** → a folder named after the link file.
- **Single scripts:** My Drive → Personal → **TikTok Videos** → **Single videos**.

If you make a video again, the file in Drive is replaced, so you won't get duplicates. Setup takes about 5 minutes, once. You don't need a Google developer account.

## 1. Make the Drive helper (in your Google account)
1. Go to **script.google.com** (signed in to the Google account whose Drive you want) and click **New project**.
2. Delete what's in the editor. Paste everything from `clip-maker/drive/apps-script.js`.
3. On the line `const PASSWORD = 'PUT-A-LONG-RANDOM-PASSWORD-HERE';`, replace the text between the quotes with a long made-up password, for example 30 random letters and numbers. Keep it; you need it in step 3.
4. Click the save icon. At the top, pick **setup** in the function menu and press **Run**. Google asks for permission: pick your account, then **Advanced** → **Go to (project name)** → **Allow**. This lets the helper put files in your Drive. The log at the bottom should say "Videos will go in: TikTok Videos".
5. Click **Deploy** → **New deployment**. Click the gear next to "Select type" and choose **Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**. It's safe because it does nothing without your password.
   - Click **Deploy**, then copy the **Web app URL** (it ends in `/exec`).

## 2. Give GitHub the link
In this repo on GitHub: **Settings → Secrets and variables → Actions → New repository secret**.
- Name `GDRIVE_URL`. Secret: the Web app URL.

## 3. Give GitHub the password
Add one more secret the same way:
- Name `GDRIVE_PASSWORD`. Secret: the password from step 1.3.

That's it. The next video you make also shows up in Drive. If something is wrong, the video still goes to the Releases page as usual, and the "Put it in Google Drive" step of the run says what happened.

**To stop it:** delete the two secrets, or in the Apps Script go to **Deploy → Manage deployments** and archive it.
