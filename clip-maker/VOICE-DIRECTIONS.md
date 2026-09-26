# Voice directions

You can tell the voice **how** to say each line by adding a few simple marks to your script. The video maker reads them and changes the voice. None of the marks are shown on screen.

A script without any marks still works exactly as before.

## The marks

**1. A mood tag at the start of a line: `[feeling]` or `[feeling, speed]`**

| Feeling | Sounds like |
|---|---|
| `calm` | quiet, gentle |
| `soft` | tender, warm |
| `sad` | heavy, a bit slower |
| `normal` | the usual voice |
| `firm` | strong, sure |
| `intense` | big emotion, for the strongest lines |

Speeds: `slow`, `normal`, `fast`.

- Lines without a tag keep the last tag.
- A new tag starts fresh: `[sad]` after `[soft, slow]` means sad at normal speed.
- A tag can also sit alone on its own line; then it counts for the lines below it.

**2. Stars around a word: `*word*`**

The voice leans on that word: a bit slower and louder. The word is also shown biggest on screen. Use it for at most one word per line.

**3. A pause inside a line: `(pause)` or `(long pause)`**

`(pause)` is about half a second and `(long pause)` is about one second. Blank lines between lines still work as before: one blank line is a short pause, and two or more are a longer pause.

## Example

```
look: moody
clips: animated
---
[soft, slow] Sometimes moving on from someone toxic
doesn't feel good (pause) at first.

[sad] You miss them. Even though they *hurt* you.


[firm] But you were *never* supposed to earn being cared for.
[intense, slow] You deserved it (long pause) the whole time.
```

## Paste this into your Claude script writer

Add this to the end of your script formula (your Claude project's instructions):

```
VOICE DIRECTIONS (always include these; my video maker reads them to change the voice)
Before writing, read the comments I give you and note the main feelings in them
(hurt, anger, relief, hope, shame, pride...). Let those feelings pick the voice marks:
- Start the script with a tag, and add a new tag whenever the mood changes:
  [feeling] or [feeling, speed]
  Feelings: calm, soft, sad, normal, firm, intense. Speeds: slow, normal, fast.
  Use them like this:
    pain, loss, loneliness, missing someone      -> [sad, slow] or [soft, slow]
    comfort, "you're not alone", gentle truths   -> [soft] or [calm]
    facts, lists, setting up the story           -> [normal]
    boundaries, "you deserve", "stop", decisions -> [firm]
    the turning point, the strongest line        -> [intense] (once or twice per script, at most)
  Build the mood: start sad, soft or calm; move to firm; save intense for the peak near the end.
- Put *stars* around the ONE word in a line that carries the feeling
  (never, always, deserve, enough, you, them, still...). About 1 line in 3 gets one. Never more than one per line.
- Use (pause) right before a hard truth or a twist, and (long pause) at most once, before the biggest line.
- Keep my usual format: one short line per clip, blank lines between thoughts,
  two blank lines for a longer pause. Use no other brackets, symbols, emojis or stage directions.
- Put the whole script in one code block so I can copy it.
```
