# The Plot Sickens Podcast — Website

Marketing site for **The Plot Sickens**, a podcast by Deltra and Vanessa, two friends living
with metastatic breast cancer who review how Hollywood depicts illness.

Live site: https://theplotsickenspodcast.com

## Stack

One static page. No build step, no package manager, no dependencies beyond two CDNs
(Tailwind Play CDN + Google Fonts).

```
index.html    the entire site — head/meta + JSON-LD, <style>, sections, one <script>
images/       logo, photos, metastatic ribbon
scripts/      RSS -> episode-card sync (stdlib Python, run by CI only)
CLAUDE.md     working notes for editing this file safely
```

## New episodes publish themselves

A GitHub Action checks the podcast's RSS feed every day at 14:00 UTC. When a new episode
appears it adds the card, updates the "EP. NN" hero badge and episode counter, trims the
oldest card, and pushes — the live site follows a few minutes later. Nothing to run by hand.

Existing cards are never rewritten, so any blurb you polish stays polished.

To see what it would do, or to run it early:

```powershell
python scripts/update_episodes.py --dry-run
```

Optional: add `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` under
**Settings → Secrets and variables → Actions** so new cards deep-link to the exact Spotify
episode instead of the show page.

## Preview locally

```powershell
Start-Process index.html        # file:// works — every path is relative
python -m http.server 8000      # only if you need http://
```

## Deploy

Serve the repo root as-is. Any static host works (GitHub Pages, Netlify, Cloudflare Pages) —
`index.html` is the entry point and there is nothing to compile.
