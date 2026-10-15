# New-hire video: "A day on the print team" (walkthrough script, first draft)

**Purpose:** show a new hire, step by step, what the printer job really is.
**Style:** the big-head cartoon girl from `skits/animation` (the pop-art style), in a fake print room.
**Length:** about 2 minutes, vertical 9:16. One narrator voice says each step while the girl does it.
**Rule:** no customer names and no staff names anywhere. Everything below comes from the print logs.
Lines marked **[was a guess, now confirmed or noted below]** are my guess from the logs. The logs show what was printed, not what the hands did.

## What the logs show (Oct 14 print PC, Oct 13 print PC)
- **Day starts with maintenance prints.** At 7:43 there were 4 "Maintenance" jobs (0 pages) in 8 seconds, then 3 more by 10:08. (confirmed: nozzle print checks and cleanings)
- **File names carry the order.** `Name - 30 - FLAT.indd` = order quantity (30) and style (FLAT, INVITE, FLD). `RA - Name - 30 - WHITE.indd` = a matching envelope job, and the last word is the paper color (WHITE, KRAFT, NAVY, SLATE...). (confirmed: RA = return address, printed on the envelopes)
- **Test first, then the run.** Almost every order starts with a 1-copy job, then the rest. A 120-card order went out as 1 + 34 + 5 + 40 + 40. A 130-card order as 1 + 39 + 40 + 35 + 15.
- **Three printers at once.** LEFT SIDE, RIGHT SIDE and an XTRA printer. Envelope (RA) jobs mostly go to the XTRA one. Jobs on different printers start only seconds apart.
- **Shipping labels in bursts.** A 4x6 label printer (about 159 x 104 mm). On Oct 13 there were about 19 labels between 11:08 and 11:56.
- **Volume.** The Oct 14 sheet has about 297 print jobs, and the Oct 13 sheet about 211. About 100 jobs happened in the first 2.5 hours (7:43 to 10:08).

## The walkthrough (each step = one scene)

| # | Scene (what we see) | Narration (what the voice says) | Log evidence |
|---|---|---|---|
| 0 | Morning, print room, three printers and a label printer, coffee on the desk. She waves. | "Welcome to the print room. Here's what a normal day looks like, step by step." | day starts 7:43 |
| 1 | She goes to each printer and taps a button. A tiny test strip comes out. | "Step one: wake up the printers. We run a quick maintenance print on each one, so the ink flows clean all day." | 4 maintenance jobs at 7:43, more at 7:51, 8:25, 9:49 |
| 2 | Computer screen: a list of order files. A big number and a style word are highlighted in each name. | "Step two: open the day's orders. Every file name tells you two things: how many to print, and what style." | file names like "- 30 - FLAT" |
| 3 | Zoom on a file name: "30" glows, then "FLAT", then a paper-color word. | "The number is the quantity. The last word is the style, or the envelope color. Read it before you print anything." | naming pattern |
| 4 | She points left, right, then to the XTRA printer. Cards slide to the side printers, envelopes to the XTRA one. | "Step three: pick the printer. Flat cards go to the left or right printer. Envelopes go to the extra printer." | RA jobs mostly on XTRA |
| 5 | She loads paper (a card stack, then a pile of envelopes in the right color). | "Load the right paper first. Card stock for cards, the right color for envelopes." [confirm] | paper size + color in names |
| 6 | One copy slides out. She holds it up to the light, nods, thumbs up. | "Step four: print ONE copy first. Check the colors and the edges. If it's good, go." | first job per order = 1 copy |
| 7 | She presses print, a counter climbs: 40, 40, 40. A mini progress bar fills. | "Step five: print the rest. Big orders go out in batches, about forty at a time, so nothing jams." | 120 = 1+34+5+40+40 |
| 8 | Split screen: left printer running, right printer running, she sets up the next order at the desk. | "While one printer runs, set up the next one. Keep all three printers working." | jobs seconds apart on different printers |
| 9 | A matching envelope prints with a small return address in the corner. She stacks card + envelope. | "Step six: print the matching envelopes. Same quantity, same order." | RA jobs match the card quantity |
| 10 | Label printer spits out a 4x6 label. She presses it onto a box. Labels pop out one after another. | "Step seven: shipping labels. As boxes get packed, print the labels and stick them on." | label bursts, 19 in 48 min |
| 11 | She does a quick maintenance print again, then back to the desk. | "Every hour or two, run a maintenance print so a clogged nozzle never ruins an order." [confirm] | maintenance jobs through the morning |
| 12 | Cart of finished boxes rolls away. She sits back, smiles. Counter on screen: "about 300 jobs today". | "That's the day: check, test, print, pack. Repeat. You'll do it all day, and you'll get fast at it." | ~297 jobs on Oct 14 |

## What the logs can NOT tell us (ask the team before we film or animate)
- How the order files get to the computer. Do they get downloaded, or sent?
- How paper and ink are loaded and when they run out.
- How prints are checked, trimmed, sorted and packed.
- What happens when a print goes wrong and has to be redone. (A few orders were printed twice, which could be a reprint.)
- Who this person works with, and how many orders a new hire is expected to handle.

## Open questions for you
1. Is "RA" return address? Are the maintenance prints nozzle cleaning?
2. Do you want this exact wording, or friendlier ("hey, you!") and shorter (60 seconds)?
3. Should the girl have a name, and should the room look like your real room (colors, logo)?

## Update (after your answers)
- Confirmed: **RA = return address** (printed on the envelopes). **Maintenance = nozzle print checks or cleanings.**
- The narrator is **Sally**. The room is a polished version of your real print room: white desks, shelves of color-coded envelope boxes, a window, gold lights, pink and navy brand colors.
- The video runs as long as it needs to cover the full process, then explains that it repeats. The final narration is in `new-hire/animation/lines.json` (21 lines, about 3 minutes).
- The steps now also use your own hiring video, in your words: mail bin by your desk, quality and accuracy check before the full print, count out the envelopes while it prints, check every single sheet, handle with care, inserts (branding card, thank you card, accuracy card showing who did the order), branding sticker on every package, then the label.
