# Chapter JSON schema (one file per chapter: chNN.json)
{
  "id": "ch01",
  "number": 1,
  "title": "The Hunger Laws",                 // short, catchy
  "subtitle": "Turn hunger down instead of fighting it",
  "law": "You don't beat hunger with willpower. You turn the volume down.",  // the chapter's "Skinny Law", 1 sentence, quotable
  "intro": "2-4 short paragraphs, plain English, second person, warm + a bit bold. Paragraphs separated by \n\n",
  "hacks": [
    {
      "title": "The Veggie-First Rule",       // 2-5 words, memorable name
      "hook": "One line that makes someone want to read it (max 18 words).",
      "what": "What to do, 2-4 sentences.",
      "why": "Why it works in plain English, 2-4 sentences. Mention the real science simply (e.g. 'a 2015 study at Weill Cornell found...') ONLY if you are confident it is real and not retracted.",
      "how": ["Step 1 short", "Step 2 short", "Step 3 short"],   // 2-4 concrete steps
      "pro": "Optional one-line pro tip or variation (or empty string)",
      "tags": ["hunger","quick-win"]          // pick 1-3 from: quick-win, hunger, cravings, kitchen, eating-out, drinks, sleep, stress, movement, mindset, bloat, shape, maintenance, shopping, social
    }
  ],
  "mythBust": { "myth": "Common belief", "truth": "What is actually true, 2-3 sentences." },
  "tryThis": { "title": "Tonight's Try-This", "text": "One small concrete challenge for today, 1-3 sentences." },
  "journal": ["Prompt 1?", "Prompt 2?", "Prompt 3?"],
  "quote": "One short, beautiful, screenshot-worthy line for a quote page (max 16 words)."
}
