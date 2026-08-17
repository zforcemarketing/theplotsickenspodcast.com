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
CLAUDE.md     working notes for editing this file safely
```

## Preview locally

```powershell
Start-Process index.html        # file:// works — every path is relative
python -m http.server 8000      # only if you need http://
```

## Deploy

Serve the repo root as-is. Any static host works (GitHub Pages, Netlify, Cloudflare Pages) —
`index.html` is the entry point and there is nothing to compile.
