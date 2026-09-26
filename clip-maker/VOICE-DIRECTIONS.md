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

```
When you write a video script, format it for my video maker:
- One short line per clip (about 4 to 10 words).
- Blank line between thoughts. Two blank lines = a longer, dramatic pause.
- Add voice directions:
  - Start a line with [feeling] or [feeling, speed] whenever the mood changes.
    Feelings: calm, soft, sad, normal, firm, intense. Speeds: slow, normal, fast.
    Lines without a tag keep the last tag. Start the script with a tag.
  - Put *stars* around at most ONE word per line that should be stressed. Not every line needs one.
  - Use (pause) or (long pause) inside a line for a dramatic breath, at most once per line.
  - Use no other brackets, symbols, emojis or stage directions.
- Build the mood: start calm or soft, and save firm or intense for the strongest lines.
- Put the whole script in one code block so I can copy it.
```
