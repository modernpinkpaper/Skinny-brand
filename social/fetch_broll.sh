#!/bin/sh
# Downloads the free Mixkit b-roll clips listed in broll_library.json (Mixkit free license) into social/broll/
cd "$(dirname "$0")" && mkdir -p broll
python3 -c "import json;[print(k,v) for k,v in json.load(open('broll_library.json')).items()]" | while read k id; do
  [ -s "broll/$k.mp4" ] || curl -sS -m 120 -o "broll/$k.mp4" "https://assets.mixkit.co/videos/$id/$id-720.mp4"
done
