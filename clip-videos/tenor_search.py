#!/usr/bin/env python3
"""Search Tenor for clips without an API key. Prints each result's mp4 link, length and a short description
(the description says "cartoon", "anime" etc., which helps pick animated-only clips).
Usage: python3 clip-videos/tenor_search.py "spongebob sad" "anime rain" ...
Then check picks with motion_check.py and paste the links into <folder>/clips.txt."""
import re, sys, requests, urllib.parse

def search(q):
    u = "https://tenor.com/search/" + urllib.parse.quote(q.replace(" ", "-")) + "-gifs"
    s = requests.get(u, headers={"User-Agent": "Mozilla/5.0"}).text.replace("\\u002F", "/")
    parts = s.split('"content_description":"'); out, seen = [], set()
    for prev, cur in zip(parts, parts[1:]):
        urls = re.findall(r'"mp4":\{"url":"(https://media\.tenor\.com/[^"]+\.mp4)","duration":([\d.]+)', prev[-6000:])
        if not urls: continue
        url, d = urls[-1]
        if url in seen: continue
        seen.add(url); out.append((url, float(d), cur.split('"', 1)[0]))
    return out

if __name__ == "__main__":
    for q in sys.argv[1:]:
        print("##", q)
        for u, d, desc in search(q)[:16]:
            print(f"  {d:4.1f}s {u}\n        {desc}")
