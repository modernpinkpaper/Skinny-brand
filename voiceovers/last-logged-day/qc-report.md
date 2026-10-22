# Quality-control report: "My last logged day"

Voice: your voice, made with **Chatterbox Nano** (110M, the Turbo-family model) on CPU.
Length: 56 seconds. Tone: warm and conversational, intensity 5/10.

## What the script says (and where it came from)
The script uses the commit history (the "log") of this repo. The last recorded day is **Sunday, October 11, 2026**, not Friday.

- Sunday's log shows one automatic run at 8:59 a.m. New York time. It sent 3 videos to your TikTok drafts:
  "Being needed is not being loved", "Help is the sunny side of control", "The mortifying ordeal of being known".
- Friday, Oct 9 was a similar run (2 videos). Saturday, Oct 10 sent 3.
- The sent list holds **44 videos** in total.
- The log only shows the automatic run on those days. It records nothing you did by hand, so the script says "my system" did the work.
- The last two lines ("A quiet day in the log is not an empty day...") are a reflection I wrote. Change them if they don't sound like you.

The brief fields were blank, so I chose: audience = you and your followers, about one minute, warm, intensity 5, ending = a quiet reflective close.

## Results

| Check | Result |
|---|---|
| Words vs clean script (small.en transcriber) | 0% word error |
| Words vs clean script (medium.en transcriber) | 0% word error |
| Cue words spoken by accident | None heard |
| Clipped samples | 0 |
| Peak level | -4.3 dBFS (limit: below -3 dBFS) |
| Loudness | -27.3 LUFS, matched to your warm reference clip (-27.3) |
| Voice match to your original recording | 0.95 out of 1 (the five tone clips scored 0.93 to 0.97) |
| Edit joins | No jumps found. Largest spike is a normal "t" sound, not an edit. |
| Seeds | Primary seed 1947. Fallback seeds were used on 4 of 14 phrases. |

## Fixes made automatically
- **Wrong word:** "Just before nine" came out as "not morning" on seed 1947. Re-made with seed 1948.
- **Wrong word:** "Forty-four videos sent so far" came out as "44 videos since so far" three times. Seed 2051 was clean.
- **Missing word:** "A quiet day..." lost its first word on seed 1947. Re-made with seed 1948.
- **After joining:** the full recording is checked again after assembly. In an earlier build "eleventh" was spoken as "eleven"; in the final build one phrase lost "and". Each time the phrase was re-made and the whole file re-checked until both transcribers matched.
- **Too fast:** my first full render spoke at about 220 words per minute. You speak at about 120 to 200. I slowed the base speed to 0.82x so it now runs at about 150 words per minute overall, close to your own pace.
- **Orphan line:** "That's it." scored badly alone on voice match, so it is now joined to the next sentence.
- **Start and end:** added a 0.3 second lead-in and 0.55 second tail.

## Pacing
- Every sentence has three speed zones (opening, body, ending), cut at quiet points between words, with 20 ms crossfades.
- Speeds run from **0.91x to 1.10x** (before the base 0.82x). Pitch is preserved.
- Every paragraph has zones above and below 1.0x. The build paragraph is the fastest. The final paragraph ends slowest (0.91x).
- Pauses: 250 to 650 ms between sentences; the longest comes before the final key point.

## What I could not check
- **I cannot listen to audio.** All checks are automatic: two transcribers, level and click measurements, and a voice-match score. Please listen once before posting.
- No "approved generated recording" was attached, so I used your own natural recordings as the pace guide.
- All sections use your **warm** reference clip, because the tone is warm throughout. This avoids voice jumps between sections.
- Chatterbox Nano has no way to tell it to whisper or stress a word, so emphasis comes only from the pacing cues.
- Chatterbox adds a hidden watermark that marks the audio as AI-made. I left it on.

Details for every attempt are in `qc-details.json`.
