#!/usr/bin/env python3
"""
Sync the episode carousel in index.html with the podcast's RSS feed.

Run by .github/workflows/update-episodes.yml on a daily cron. Adds a card for any
episode in the feed that isn't on the page yet, demotes the old "NEW" badge to a
date, refreshes the hero badge and the episode counter, and trims the oldest card.

Only *new* episodes are ever written. Existing cards are left byte-for-byte alone,
so hand-polished blurbs and one-off badges (ep 27's 1-YR ANNIVERSARY) survive.

Standard library only — the site has no build step and this script keeps it that way.

Usage:
    python scripts/update_episodes.py --dry-run    # print what would change
    python scripts/update_episodes.py              # write index.html
"""

import argparse
import base64
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

RSS_URL = "https://anchor.fm/s/f5983dc0/podcast/rss"
APPLE_PODCAST_ID = "1817231716"
SPOTIFY_SHOW_ID = "38xOqaOpRi8lMpDoZJsM51"

SHOW_SPOTIFY_URL = f"https://open.spotify.com/show/{SPOTIFY_SHOW_ID}"
SPOTIFY_EPISODE_BASE = "https://open.spotify.com/episode/"
SHOW_APPLE_URL = f"https://podcasts.apple.com/us/podcast/the-plot-sickens/id{APPLE_PODCAST_ID}"

# The public show page returns its full HTML only to a browser-shaped User-Agent.
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# Keep the carousel from growing without bound (see CLAUDE.md "Adding an episode").
MAX_CARDS = 5

# Card blurbs are ~100-160 chars on the existing cards; keep generated ones in range.
BLURB_TARGET = 170
BLURB_HARD_CAP = 200

ITUNES_NS = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

SPOTIFY_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" class="text-[var(--gold-light)]"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm4.59 14.4a.63.63 0 0 1-.86.21c-2.37-1.45-5.36-1.78-8.87-.97a.63.63 0 1 1-.28-1.22c3.84-.88 7.14-.5 9.8 1.12.3.18.4.57.21.86Zm1.22-2.72a.78.78 0 0 1-1.08.26c-2.71-1.67-6.85-2.15-10.06-1.18a.78.78 0 1 1-.45-1.5c3.67-1.11 8.23-.57 11.33 1.34.37.23.49.72.26 1.08Zm.11-2.83C14.98 9 8.98 8.8 5.6 9.83a.94.94 0 1 1-.55-1.8c3.88-1.18 10.46-.94 14.58 1.51a.94.94 0 0 1-.71 1.7 1 1 0 0 1-.31-.1Z"/></svg>'

APPLE_ICON = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" class="text-[var(--gold-light)]"><path d="M5.34 0A5.328 5.328 0 000 5.34v13.32A5.328 5.328 0 005.34 24h13.32A5.328 5.328 0 0024 18.66V5.34A5.328 5.328 0 0018.66 0zm6.525 2.568c2.336 0 4.448.902 6.056 2.587 1.224 1.272 1.912 2.619 2.264 4.392.12.59.12 2.2.007 2.864a8.506 8.506 0 01-3.24 5.296c-.608.46-2.096 1.261-2.336 1.261-.088 0-.096-.091-.056-.46.072-.592.144-.715.48-.856.536-.224 1.448-.874 2.008-1.435a7.644 7.644 0 002.008-3.536c.208-.824.184-2.656-.048-3.504-.728-2.696-2.928-4.792-5.624-5.352-.784-.16-2.208-.16-3 0-2.728.56-4.984 2.76-5.672 5.528-.184.752-.184 2.584 0 3.336.456 1.832 1.64 3.512 3.192 4.512.304.2.672.408.824.472.336.144.408.264.472.856.04.36.03.464-.056.464-.056 0-.464-.176-.896-.384l-.04-.03c-2.472-1.216-4.056-3.274-4.632-6.012-.144-.706-.168-2.392-.03-3.04.36-1.74 1.048-3.1 2.192-4.304 1.648-1.737 3.768-2.656 6.128-2.656zm.134 2.81c.409.004.803.04 1.106.106 2.784.62 4.76 3.408 4.376 6.174-.152 1.114-.536 2.03-1.216 2.88-.336.43-1.152 1.15-1.296 1.15-.023 0-.048-.272-.048-.603v-.605l.416-.496c1.568-1.878 1.456-4.502-.256-6.224-.664-.67-1.432-1.064-2.424-1.246-.64-.118-.776-.118-1.448-.008-1.02.167-1.81.562-2.512 1.256-1.72 1.704-1.832 4.342-.264 6.222l.413.496v.608c0 .336-.027.608-.06.608-.03 0-.264-.16-.512-.36l-.034-.011c-.832-.664-1.568-1.842-1.872-2.997-.184-.698-.184-2.024.008-2.72.504-1.878 1.888-3.335 3.808-4.019.41-.145 1.133-.22 1.814-.211zm-.13 2.99c.31 0 .62.06.844.178.488.253.888.745 1.04 1.259.464 1.578-1.208 2.96-2.72 2.254h-.015c-.712-.331-1.096-.956-1.104-1.77 0-.733.408-1.371 1.112-1.745.224-.117.534-.176.844-.176zm-.011 4.728c.988-.004 1.706.349 1.97.97.198.464.124 1.932-.218 4.302-.232 1.656-.36 2.074-.68 2.356-.44.39-1.064.498-1.656.288h-.003c-.716-.257-.87-.605-1.164-2.644-.341-2.37-.416-3.838-.218-4.302.262-.616.974-.966 1.97-.97z"/></svg>'


# ---------------------------------------------------------------- fetching


def fetch(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "plot-sickens-site-updater"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_feed():
    """Parse the RSS feed into a list of episode dicts, newest first."""
    root = ET.fromstring(fetch(RSS_URL))
    episodes = []
    for item in root.findall("./channel/item"):
        number = text_of(item.find(f"{ITUNES_NS}episode"))
        title = text_of(item.find("title"))
        if not title:
            continue
        try:
            published = parsedate_to_datetime(text_of(item.find("pubDate")))
        except (TypeError, ValueError):
            continue
        episodes.append(
            {
                "number": int(number) if number and number.isdigit() else None,
                "raw_title": title,
                "title": clean_title(title),
                "published": published,
                "runtime": format_duration(text_of(item.find(f"{ITUNES_NS}duration"))),
                "blurb": make_blurb(
                    text_of(item.find("description"))
                    or text_of(item.find(f"{ITUNES_NS}summary"))
                ),
            }
        )
    episodes.sort(key=lambda e: e["published"], reverse=True)
    return episodes


def fetch_apple_links():
    """Map normalized episode title -> Apple Podcasts episode URL. No auth required."""
    url = (
        "https://itunes.apple.com/lookup?"
        + urllib.parse.urlencode({"id": APPLE_PODCAST_ID, "entity": "podcastEpisode", "limit": 200})
    )
    try:
        data = json.loads(fetch(url))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        warn(f"Apple lookup failed ({exc}); cards will fall back to the show page.")
        return {}

    links = {}
    for result in data.get("results", []):
        if result.get("wrapperType") != "podcastEpisode":
            continue
        name, view_url = result.get("trackName"), result.get("trackViewUrl")
        if not name or not view_url:
            continue
        links[normalize(name)] = view_url.split("&uo=")[0]
    return links


def scrape_spotify_links():
    """
    Map normalized episode title -> open.spotify.com episode URL, without credentials.

    The public show page server-renders its most recent episodes into a base64
    <script id="initialState"> blob carrying each episode's name and spotify:episode:
    URI. That is far more than this script ever needs, and unlike the Web API it needs
    no client id/secret -- Spotify has required the account registering a developer app
    to hold Premium since February 2026.

    Returns {} on any failure, so main() falls back to the show-level URL.
    """
    try:
        page = fetch(
            SHOW_SPOTIFY_URL,
            headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"},
        ).decode("utf-8", "replace")
        blob = re.search('<script id="initialState"[^>]*>(.*?)</script>', page, re.S)
        if not blob:
            warn("Spotify show page had no initialState blob; falling back to the show page.")
            return {}
        data = json.loads(base64.b64decode(blob.group(1).strip()).decode("utf-8"))
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        warn(f"Spotify show page scrape failed ({exc}); falling back to the show page.")
        return {}

    links = {}

    def walk(node):
        if isinstance(node, dict):
            uri, name = node.get("uri"), node.get("name")
            if isinstance(uri, str) and uri.startswith("spotify:episode:") and name:
                links[normalize(name)] = f"{SPOTIFY_EPISODE_BASE}{uri.rsplit(':', 1)[-1]}"
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(data)
    return links


def fetch_spotify_links():
    """Prefer the credential-free show-page scrape; fall back to the Web API."""
    links = scrape_spotify_links()
    if links:
        note(f"Matched {len(links)} Spotify episode links from the public show page.")
        return links
    return fetch_spotify_links_api()


def fetch_spotify_links_api():
    """
    Same mapping via the official Web API. Fallback for when the scrape stops working.

    Needs SPOTIFY_CLIENT_ID / SPOTIFY_CLIENT_SECRET because the RSS <link> points at
    the creators.spotify.com backend, not the public episode page. Without credentials
    this returns {} and cards fall back to the show-level Spotify URL, which the
    data-listen modal already handles.
    """
    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
    if not (client_id and client_secret):
        note("No Spotify credentials set; new cards will link to the show page.")
        return {}

    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    try:
        req = urllib.request.Request(
            "https://accounts.spotify.com/api/token",
            data=b"grant_type=client_credentials",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "plot-sickens-site-updater",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            token = json.loads(resp.read()).get("access_token")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        warn(f"Spotify auth failed ({exc}); falling back to the show page.")
        return {}

    if not token:
        warn("Spotify returned no access token; falling back to the show page.")
        return {}

    links = {}
    url = (
        f"https://api.spotify.com/v1/shows/{SPOTIFY_SHOW_ID}/episodes?"
        + urllib.parse.urlencode({"market": "US", "limit": 50})
    )
    while url:
        try:
            page = json.loads(fetch(url, headers={"Authorization": f"Bearer {token}"}))
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            warn(f"Spotify episode fetch failed ({exc}).")
            break
        for episode in page.get("items", []) or []:
            if not episode:
                continue
            name = episode.get("name")
            link = (episode.get("external_urls") or {}).get("spotify")
            if name and link:
                links[normalize(name)] = link
        url = page.get("next")
    return links


# ---------------------------------------------------------------- formatting


def text_of(element):
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def normalize(value):
    """Loose key for matching titles across RSS / Apple / Spotify."""
    return re.sub(r"[^a-z0-9]+", "", html.unescape(value or "").lower())


def clean_title(raw):
    """'Episode 32: Funny People' -> 'Funny People'."""
    title = html.unescape(raw).strip()
    title = re.sub(r"^.*?\bepisode\s*\d+\s*[:\-–—]\s*", "", title, flags=re.IGNORECASE)
    return title.strip() or html.unescape(raw).strip()


def format_duration(raw):
    """'01:13:35' (or plain seconds) -> '1H 14M', rounded to the nearest minute."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    if ":" in raw:
        parts = [int(p) for p in raw.split(":") if p.isdigit()]
        seconds = 0
        for part in parts:
            seconds = seconds * 60 + part
    elif raw.isdigit():
        seconds = int(raw)
    else:
        return ""
    minutes = round(seconds / 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}H {minutes}M" if hours else f"{minutes}M"


def make_blurb(description):
    """Collapse the show notes into one or two sentences sized for a card."""
    text = re.sub(r"<[^>]+>", " ", description or "")
    text = html.unescape(text)
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    sentences = re.findall(r"[^.!?]+[.!?]*", text)
    blurb = ""
    for sentence in sentences:
        candidate = (blurb + " " + sentence).strip() if blurb else sentence.strip()
        if blurb and len(candidate) > BLURB_TARGET:
            break
        blurb = candidate
        if len(blurb) >= BLURB_TARGET:
            break

    blurb = re.sub(r"\s+", " ", blurb).strip() or text
    if len(blurb) > BLURB_HARD_CAP:
        blurb = blurb[:BLURB_HARD_CAP].rsplit(" ", 1)[0].rstrip(",;:-") + "…"
    return blurb


def esc_text(value):
    return html.escape(value, quote=False)


def esc_attr(value):
    return html.escape(value, quote=True)


def short_date(when):
    return f"{when.strftime('%b').upper()} {when.day}"


# ---------------------------------------------------------------- card building


def build_card(episode, spotify_url, apple_url, is_newest):
    """Render one .episode-card, matching the hand-written cards exactly."""
    number = episode["number"]
    label = f"Episode {number}" if number else episode["title"]
    badge = f"EPISODE {number}" if number else "NEW EPISODE"
    listen_title = f"Episode {number} · {episode['title']}" if number else episode["title"]

    # Primary href must stay real so the card still works with JS disabled.
    primary = spotify_url or apple_url or SHOW_SPOTIFY_URL
    icon = APPLE_ICON if (apple_url and not spotify_url) else SPOTIFY_ICON

    data_attrs = ""
    if spotify_url:
        data_attrs += f' data-spotify="{esc_attr(spotify_url)}"'
    if apple_url:
        data_attrs += f' data-apple="{esc_attr(apple_url)}"'

    meta = " · ".join(
        part for part in (episode["runtime"], "NEW" if is_newest else short_date(episode["published"])) if part
    )

    href = esc_attr(primary)
    title_attr = esc_attr(listen_title)
    overlay_label = esc_attr(f"Listen to {label}: {episode['title']} — choose your platform")
    play_label = esc_attr(f"Play {label} — choose your platform")

    return f"""          <!-- {label} -->
          <div class="episode-card relative shrink-0 w-[280px] sm:w-[320px] rounded-2xl overflow-hidden bg-[var(--ink-2)] border border-[var(--gold-dark)]/30">
            <div class="frame-holes"></div>
            <a href="{href}" target="_blank" rel="noopener noreferrer" class="absolute inset-0 z-0"
               data-listen{data_attrs} data-listen-title="{title_attr}"
               aria-label="{overlay_label}"></a>
            <div class="relative z-[1] pointer-events-none px-5 pt-5 pb-4">
              <span class="ticket-badge inline-block font-tag text-xs px-3 py-1 rounded-full">{esc_text(badge)}</span>
              <h3 class="font-display font-bold text-xl text-[var(--gold-light)] mt-3 leading-tight">{esc_text(episode['title'])}</h3>
              <p class="text-[var(--cream)]/70 text-sm mt-2 leading-relaxed">{esc_text(episode['blurb'])}</p>
              <p class="font-tag text-xs text-[var(--gold-dark)] mt-3 tracking-wider">{esc_text(meta)}</p>
            </div>
            <div class="relative z-10 flex items-center gap-3 px-5 pb-5 pointer-events-none">
              <a href="{href}" target="_blank" rel="noopener noreferrer"
                 data-listen{data_attrs} data-listen-title="{title_attr}"
                 aria-label="{play_label}" class="pointer-events-auto p-2 rounded-full bg-black/30 hover:bg-[var(--curtain)] transition-colors" style="min-width:40px;min-height:40px;display:flex;align-items:center;justify-content:center;">
                {icon}
              </a>
            </div>
          </div>
"""


# ---------------------------------------------------------------- page editing


def split_track(page):
    """Return (before, [card blocks], after) around the contents of #epTrack."""
    open_match = re.search(r'<div id="epTrack"[^>]*>', page)
    if not open_match:
        die("Could not find #epTrack in index.html.")

    # The track's closing tag is the one whose nesting depth returns to zero.
    cursor, depth = open_match.end(), 1
    tag_pattern = re.compile(r"<div\b[^>]*>|</div>")
    while depth:
        tag = tag_pattern.search(page, cursor)
        if not tag:
            die("Unbalanced <div> tags inside #epTrack.")
        depth += 1 if tag.group().startswith("<div") else -1
        cursor = tag.end()
    close_start = cursor - len("</div>")

    inner = page[open_match.end() : close_start]
    blocks = [b for b in re.split(r"(?=^[ \t]*<!-- Episode )", inner, flags=re.MULTILINE) if b.strip()]
    return page[: open_match.end()], blocks, page[close_start:]


def card_number(block):
    match = re.search(r'class="ticket-badge[^"]*"[^>]*>\s*EPISODE\s+(\d+)', block)
    return int(match.group(1)) if match else None


def demote_new_badge(blocks, by_number):
    """Replace the previous card's '· NEW' with its publish date."""
    for index, block in enumerate(blocks):
        if "· NEW<" not in block:
            continue
        number = card_number(block)
        episode = by_number.get(number)
        replacement = short_date(episode["published"]) if episode else "EARLIER"
        blocks[index] = block.replace("· NEW<", f"· {replacement}<", 1)
    return blocks


def update_counters(page, newest_number, total_episodes):
    """Refresh the hero badge and the '30+ EPISODES REVIEWED' trust line."""
    changes = []

    if newest_number:
        page, count = re.subn(
            r"(NEW EPISODE OUT NOW — EP\.\s*)\d+",
            lambda m: f"{m.group(1)}{newest_number}",
            page,
        )
        if count:
            changes.append(f"hero badge -> EP. {newest_number}")

    milestone = (total_episodes // 10) * 10
    if milestone >= 10:
        def bump(match):
            return match.group(0) if int(match.group(1)) >= milestone else f"{milestone}+ EPISODES REVIEWED"

        page, count = re.subn(r"(\d+)\+ EPISODES REVIEWED", bump, page)
        if count:
            changes.append(f"episode counter -> {milestone}+")

    return page, changes


# ---------------------------------------------------------------- plumbing


def note(message):
    print(f"  {message}")


def warn(message):
    print(f"  ! {message}", file=sys.stderr)


def die(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    parser.add_argument("--index", type=Path, default=INDEX, help="page to update (for testing)")
    args = parser.parse_args()

    index_path = args.index
    raw = index_path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    page = raw.replace("\r\n", "\n")

    print(f"Fetching {RSS_URL}")
    episodes = fetch_feed()
    if not episodes:
        die("RSS feed returned no episodes.")
    print(f"  {len(episodes)} episodes in feed; newest is #{episodes[0]['number']} {episodes[0]['title']!r}")

    before, blocks, after = split_track(page)
    existing = {n for n in (card_number(b) for b in blocks) if n}
    print(f"  {len(blocks)} cards on the page: {sorted(existing, reverse=True)}")

    missing = [e for e in episodes if e["number"] and e["number"] not in existing]
    # Only add episodes newer than what's on the page; don't backfill the archive.
    highest = max(existing) if existing else 0
    missing = [e for e in missing if e["number"] > highest]

    if not missing:
        print("Already up to date. Nothing to do.")
        return 0

    print(f"New episodes: {[e['number'] for e in missing]}")
    apple_links = fetch_apple_links()
    spotify_links = fetch_spotify_links()
    by_number = {e["number"]: e for e in episodes if e["number"]}

    blocks = demote_new_badge(blocks, by_number)

    # Oldest of the new batch first, so repeated prepends leave newest on top.
    for index, episode in enumerate(sorted(missing, key=lambda e: e["number"])):
        key = normalize(episode["raw_title"])
        spotify_url = spotify_links.get(key)
        apple_url = apple_links.get(key)
        is_newest = index == len(missing) - 1

        card = build_card(episode, spotify_url, apple_url, is_newest)
        blocks.insert(0, card)

        platforms = ", ".join(p for p, v in (("Spotify", spotify_url), ("Apple", apple_url)) if v) or "show-level fallback"
        print(f"  + EP {episode['number']} {episode['title']!r} [{episode['runtime']}] ({platforms})")
        if not episode["blurb"]:
            warn(f"EP {episode['number']} has no description in the feed; blurb is empty.")

    dropped = blocks[MAX_CARDS:]
    blocks = blocks[:MAX_CARDS]
    for block in dropped:
        print(f"  - trimmed EP {card_number(block)} (carousel capped at {MAX_CARDS})")

    cards = "\n\n".join(b.lstrip("\n").rstrip() for b in blocks)
    page = f"{before}\n\n{cards}\n\n        {after}"

    newest_number = max(e["number"] for e in missing)
    page, counter_changes = update_counters(page, newest_number, len(episodes))
    for change in counter_changes:
        print(f"  ~ {change}")

    if args.dry_run:
        print("\nDry run - index.html not written.")
        return 0

    index_path.write_bytes(page.replace("\n", newline).encode("utf-8"))
    print(f"\nWrote {index_path}")

    # Hand the episode list to the workflow for its commit message.
    summary = ", ".join(f"EP {e['number']} {e['title']}" for e in sorted(missing, key=lambda e: -e["number"]))
    if step_output := os.environ.get("GITHUB_OUTPUT"):
        with open(step_output, "a", encoding="utf-8") as fh:
            fh.write(f"updated=true\nsummary={summary}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
