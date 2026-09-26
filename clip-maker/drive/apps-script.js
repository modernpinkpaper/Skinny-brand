// Clip Maker -> Google Drive helper. Paste this whole file into a new project at script.google.com
// (see drive/README.md). It runs in YOUR Google account: when GitHub sends the right password it makes
// the folder and hands back a short-lived (1 hour) upload pass, so GitHub can put the videos in your Drive.

const PASSWORD = 'PUT-A-LONG-RANDOM-PASSWORD-HERE';   // the same text goes in the GDRIVE_PASSWORD GitHub secret
const MAIN_FOLDER_ID = '1eCb3hkd49gkxHUoKbYot4uNbKuAtU9aG';   // My Drive > Personal > TikTok Videos

function doPost(e) {
  const req = JSON.parse((e && e.postData && e.postData.contents) || '{}');
  if (PASSWORD.indexOf('PUT-A-LONG') === 0 || req.password !== PASSWORD) return reply({ error: 'wrong password' });
  const lock = LockService.getScriptLock();   // many videos finish at once: make each folder only once
  lock.waitLock(30000);
  try {
    let folder = DriveApp.getFolderById(MAIN_FOLDER_ID);
    if (req.folder) folder = folderIn(folder, String(req.folder).slice(0, 100));
    return reply({ folderId: folder.getId(), token: ScriptApp.getOAuthToken() });
  } finally {
    lock.releaseLock();
  }
}

function folderIn(parent, name) {
  const found = parent.getFoldersByName(name);
  return found.hasNext() ? found.next() : parent.createFolder(name);
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}

// Run this once from the editor (select "setup" and press Run) so Google asks for permission.
function setup() {
  Logger.log('Videos will go in: ' + DriveApp.getFolderById(MAIN_FOLDER_ID).getName());
}
