# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Marketing site for **The Plot Sickens Podcast** — Deltra & Vanessa, two friends living with
metastatic breast cancer who review how Hollywood depicts illness. One-page static site,
no build step, no dependencies beyond two CDNs (Tailwind Play CDN + Google Fonts).

Everything is in [index.html](index.html) (~1,100 lines) plus [images/](images/). There is no
`package.json`, no tests, no linter, and no host config — **do not introduce a build step.**

Canonical URL used in OG/schema tags: `https://theplotsickenspodcast.com`.

## Commands

```powershell
Start-Process index.html            # preview (file:// works — all paths are relative)
python -m http.server 8000          # only needed if testing something that requires http://
npx puppeteer screenshot index.html --fullpage   # visual check / reference-match rounds
```

## Relationship to the ZForce playbook

The user-level playbook at `~/CLAUDE.md` governs **local home-service businesses** (phone-call
and lead-form conversion, LocalBusiness schema, service-area SEO). This project is a podcast,
so several of its mandates are deliberately translated rather than followed literally:

| Playbook says | This site does |
| --- | --- |
| Phone number + `tel:` everywhere | No phone at all — the conversion action is **Listen** |
| Sticky mobile *call* bar | Sticky mobile **Spotify / Apple Podcasts** bar |
| Lead form ≤ 5 fields | No form; contact happens via Instagram DM |
| `LocalBusiness` JSON-LD, service areas, NAP | `PodcastSeries` + `FAQPage` JSON-LD; no NAP |
| §6 metallic/industrial design system | Vintage-cinema palette (see below) — keep it |

Still in force: ≥3 CTAs down the page, 44px tap targets, reduced-motion guards, AA contrast,
FAQ schema, OG/Twitter/favicon, and listing any `[[NEEDS_INPUT]]` placeholders back to the user.

## File architecture

`index.html` is four layers, in order:

1. **`<head>` metadata** — title/description/OG/Twitter, inline SVG data-URI favicon (gold film
   reel), Google Fonts, Tailwind CDN, then **two JSON-LD blocks**: `PodcastSeries` and `FAQPage`.
2. **`<style>`** ([index.html:132-341](index.html#L132-L341)) — CSS custom properties and every
   hand-rolled effect (film grain, curtains, filmstrip dividers, carousel, listen modal).
   Tailwind utilities reference the vars as `bg-[var(--ink-2)]`, `text-[var(--gold-light)]`, etc.
3. **Body sections** — sticky mobile listen bar → header → mobile menu → `<main>` (hero,
   episodes carousel, our story, show format, where to listen, FAQ, tip jar, final CTA) →
   footer → listen modal. `.filmstrip` divs separate sections.
4. **One `<script>`** ([index.html:981](index.html#L981)) — listen-modal IIFE, curtain intro
   IIFE, then top-level blocks for mobile nav, scroll reveal, episode carousel, header shadow.

## Invariants that break silently if ignored

**FAQ content is duplicated.** Each Q&A exists twice: in the `FAQPage` JSON-LD
([index.html:51-130](index.html#L51-L130)) and in the on-page `<details class="faq-item">`
markup ([index.html:762+](index.html#L762)). Edit both or the structured data goes stale.
The JSON-LD collapses the multi-paragraph on-page answers into one `text` string.

**`data-listen` is the click contract.** Any element carrying `data-listen` is intercepted by a
delegated document click handler that opens the platform-chooser modal instead of navigating:

- `data-spotify` / `data-apple` — per-episode deep links. Whichever is absent falls back to the
  show-level URL captured once from the modal's own initial `href`s at load.
- `data-listen-title` — subtitle shown in the modal (e.g. `Episode 32 · Funny People`).
- **Every trigger must keep a real `href`** so it still works with JS disabled.

**Episode cards have a layered hit-target structure.** A full-card overlay `<a>` sits at
`absolute inset-0 z-0`; the text wrapper is `pointer-events-none` so clicks fall through to it;
the play button re-enables `pointer-events-auto`. Preserve this when editing a card.

**The carousel treats every direct child of `#epTrack` as an episode.** Dots are generated one
per child and `cardStep()` measures `cards[0].offsetWidth`. Never add a non-card element inside
the track, and keep all cards the same width (`w-[280px] sm:w-[320px]`).

**82px header height is hard-coded in three places** — `main`'s `pt-[82px]`, `#mobileMenu`'s
`top-[82px]`, and `body::after`'s `top:82px`. Changing the header's padding or logo height
(`h-14`) means updating all three.

**The mobile menu lives outside `<header>` on purpose.** The header's `backdrop-blur` makes it a
containing block for fixed descendants, which broke the menu's `bottom-0` sizing. Don't move it
back in.

**Bottom padding compensates for the fixed mobile bar** — `main` is `pb-16 sm:pb-0` and the
footer `pb-24 sm:pb-10`. Change the bar's height and these must follow.

**z-index ladder:** header/mobile menu `40` · sticky mobile bar `50` · vignette `body::after` `59`
· grain `body::before` `60` and listen modal `60`. Anything new that must sit above the modal
needs a value above 60.

**Every animation needs a `prefers-reduced-motion: reduce` guard.** Note that `.ribbon-draw`'s
reduce rule has *equal* specificity to the base rule, so it must stay physically after it in the
stylesheet ([index.html:284](index.html#L284)).

## Images

Referenced by the page: `logo.jpg`, `metastatic-ribbon.png` (declared `400×760`),
`deltra-ness-1.jpg`, `deltra-ness-2.jpg`.

The space-and-capital filenames (`The Plot Sickens Podcast Logo.jpeg`, `Deltra & Ness 1.jpeg`,
`Metastatic ribbon.jpeg`) are the **originals** — byte-identical to the lowercase web-safe copies.
Always reference the lowercase names; add a lowercase copy when the client sends a new original.

`ribbon-form.gif` (2.7 MB), `ribbon-string.gif`, `ribbon-string2.gif` are abandoned ribbon-animation
experiments, unused. Don't wire them in — the CSS `clip-path` `ribbonUnroll` animation replaced them.

Logo and photo `<img>` tags carry `onerror` fallbacks to `placehold.co`; keep them when swapping
sources so a bad path degrades visibly rather than blankly.

## Design tokens

Defined on `:root` — vintage cinema: dark ink browns, gold, theater-curtain red, plus lavender/pink
for the metastatic-ribbon accents.

`--ink #150b08` · `--ink-2 #1f1210` · `--header-bg #6b4a38` · `--panel #241512` ·
`--curtain #6e1c1c` (`-light #8f2a2a`, `-dark #4a1414`) · `--gold #e3c08a` (`-light #f3ddb0`,
`-dark #b6935f`) · `--cream #f6ecd9` · `--lavender #b9a3d6` · `--pink #ec9cc0`

Type roles: `.font-display` = Playfair Display (headings, italic pull-quotes) · `.font-tag` =
Bebas Neue (eyebrows, buttons, nav, all-caps labels) · body = Inter.
Button classes: `.btn-gold`, `.btn-gold-bright` (header LISTEN NOW), `.btn-outline`.

## Editorial notes

- The **metastatic** ribbon is used instead of the pink ribbon, deliberately and explained twice
  on the page (Our Story callout + FAQ). Never substitute a generic pink ribbon or reframe this.
- "Deltra and Vanessa" in prose; the badge under the photos reads `DELTRA 🎬 VANESSA`.
- Episode cadence copy is "every other week" / "bi-weekly-ish, health permitting" — keep the
  health caveat.

## Automatic episode updates

`.github/workflows/update-episodes.yml` runs `scripts/update_episodes.py` daily (14:00 UTC)
and pushes straight to `main`; Pages redeploys itself. **Adding an episode is normally hands-off
— the steps below are the manual fallback.**

The script reads the Anchor RSS feed (`https://anchor.fm/s/f5983dc0/podcast/rss`, discovered via
Apple's lookup API for podcast id `1817231716`) and:

- adds a card for any episode numbered **higher** than the highest already on the page,
- demotes the previous `· NEW` badge to that episode's publish date,
- updates the hero `EP. NN` badge and the `NN+ EPISODES REVIEWED` counter (never downward),
- trims `#epTrack` back to `MAX_CARDS` (5).

**It only ever prepends.** Existing cards are never rewritten, so hand-polished blurbs and
one-off badges (ep 27's `· 1-YR ANNIVERSARY`) survive. If you improve a generated blurb by hand,
your version sticks.

Card blurbs are auto-derived from the RSS `<description>` — one or two sentences, capped at 200
chars, tags stripped, entities decoded. That reads like show notes rather than the hand-written
voice of the older cards; editing the blurb afterwards is expected and safe.

**Per-platform links.** Both come free, with no credentials.

Apple episode URLs come from the iTunes lookup API. Spotify episode URLs are *not* in the feed —
its `<link>` points at the creators.spotify.com backend — so `scrape_spotify_links()` reads the
public show page instead: `open.spotify.com/show/<id>` server-renders its ~12 most recent episodes
into a base64 `<script id="initialState">` blob holding each episode's name and `spotify:episode:`
URI. Matched to feed titles through the same `normalize()` key as the Apple links. It needs a
browser-shaped `User-Agent` (`BROWSER_UA`) — Spotify serves a stub page otherwise.

This replaced the Web API path because **since February 2026 Spotify requires the account
registering a developer app to hold Premium**, which put `SPOTIFY_CLIENT_ID` /
`SPOTIFY_CLIENT_SECRET` out of reach. `fetch_spotify_links_api()` is still there and still works
if those secrets are ever set — `fetch_spotify_links()` tries the scrape first and falls back to it.

If both paths come up empty the script omits `data-spotify` and the modal falls back to the
show-level URL, which is already the documented `data-listen` contract; those cards use the Apple
icon on the play button. So a Spotify redesign degrades the links, it does not break the build.

Test changes without touching the live page:

```powershell
python scripts/update_episodes.py --dry-run              # report only
python scripts/update_episodes.py --index path\to\copy   # write to a scratch copy
```

Because the script anchors on `<div id="epTrack">`, the `<!-- Episode NN -->` comment before each
card, and the `EPISODE NN` ticket-badge text, **those three are load-bearing** — renaming them
breaks the sync silently.

## Adding an episode (manual fallback)

1. Copy the newest `.episode-card` block to the front of `#epTrack`, updating the overlay `<a>`,
   the play button `<a>`, episode number, title, blurb, and `1H 14M · NEW` runtime/date line.
2. Set `data-spotify` and/or `data-apple` (plus `data-listen-title`) on **both** anchors, and put
   the same URL in each anchor's `href`.
3. Move `· NEW` off the previous top card and give it a date.
4. Update the hero badge `🎬 NEW EPISODE OUT NOW — EP. 32` ([index.html:423](index.html#L423)) and
   the `30+ EPISODES REVIEWED` trust line if the count crosses a round number.
5. Trim the track rather than letting it grow unbounded — the oldest card is currently ep 27.

## Open `[[NEEDS_INPUT]]`

None outstanding. Both former items are closed:

- Ep 27's Spotify link was backfilled from the public show page, so every card on the page now
  carries both `data-spotify` and `data-apple`.
- The `SPOTIFY_CLIENT_ID` / `SPOTIFY_CLIENT_SECRET` secrets are no longer needed — see
  "Per-platform links" above. Do not re-add them as a request; they now require a paid Premium
  account and buy nothing the scrape does not already provide.
