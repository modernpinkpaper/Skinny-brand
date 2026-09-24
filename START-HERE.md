# The Skinny Laws — Start Here

Everything for your TikTok page **@theskinnylaws** and your paid product is in this folder.

## Your links
- **TikTok bio link (goes straight to checkout, no other products shown):** https://modernpinkpaper.com/cart/52535817404632:1
- Product page (Unlisted, only people with the link can see it): https://modernpinkpaper.com/products/the-skinny-laws-vault
- Price: $19. Shipping is off, and it's hidden from Google and your shop's search.

## 1. The product: *The Skinny Laws Vault*

Folder: `product/dist/`

| File | What it is |
|---|---|
| `the-skinny-laws-vault.pdf` | The main download. Opens on any phone or computer. The contents page and "back to contents" links are clickable. |
| `the-skinny-laws-vault.html` | The **interactive** version. It has a menu, search, tag filters, the quiz, tick-boxes that save, a 30-day challenge and a weight tracker. Opens in any web browser (Safari, Chrome), even offline. |
| `the-skinny-laws-vault.zip` | Both files together. Upload this to your store so buyers get both. |
| `store-cover.png` | Square picture for your shop listing. |
| `shopify-listing.md` | Title, description and price idea for the shop page. Ready to copy and paste. |

**What's inside:** 12 Laws × 10 hacks = 120 hacks. Each hack has: what to do, why it works, step-by-step how-to, and a pro tip. Every Law also has a myth-buster, a "try this" challenge, 3 journal prompts and a quote page. Bonuses: eating-type quiz, 30-Day Challenge, Lean Grocery List, Restaurant Cheat Sheet, Weekly Average Tracker, "12 Laws on one page", My Favorites list, and a Safety page.

To change any wording, edit the files in `product/content/` and run:

```
python3 product/build.py && node product/make_pdf.mjs
```

## 2. The TikTok posts (7 days × 3 a day = 21 posts)

Folder: `tiktok-posts/day-1` … `day-7`. Every post has its own folder with:

- **Carousels** → `slide-01.png`, `slide-02.png`… Upload them in order in TikTok **Photo** mode.
- **Videos** → `video.mp4`, ready to post.
- `caption.txt` → post time, caption, hashtags, pinned comment and sound tip.

**Style rules (keep these when you make more):** first person, like a friend sharing what worked for *her*. lowercase, casual, not perfect grammar. provocative hook on slide 1. plain white TikTok text boxes on your photos. one girl per carousel. videos are only: typing in Notes, a text chat, or scrolling through the guide. the guide is mentioned like an afterthought ("i put it in a lil guide, its in my bio").

### Daily schedule
| Time | Slot |
|---|---|
| 7:30 AM | Post 1 |
| 12:15 PM | Post 2 |
| 8:00 PM | Post 3 |

### Tips
- Add a trending sound inside TikTok and turn it down low.
- Pin the comment from `caption.txt` right after posting.
- Reply to comments in the first hour, because early replies help the post get shown to more people.
- Put your shop link in your bio (you need 1,000 followers for a clickable bio link on a personal account. A Business account can add a link sooner in some regions. Until then, say "link in my IG bio" or use a Linktree in your Instagram).

## 3. Making more posts

All posts live in `social/posts.mjs`. Copy one, change the words, and run:

```
node social/render.mjs            # everything
node social/render.mjs d3-2       # just one post
```

## Safety note
The Vault is built to be healthy and to last. It has no starving, no crash diets, no detox teas and no pills. Keep the posts this way too. TikTok limits the reach of weight-loss content that pushes extreme dieting, so healthy content also gets seen by more people.
