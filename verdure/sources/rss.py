"""RSS event feed adapter.

Many small venues, museums, and campus calendars publish an ordinary RSS 2.0
feed for their events, often alongside (or instead of) an iCal feed. This
adapter reads that feed directly. It never follows an item's <link> to the
organizer's own page -- everything it records comes from the feed's own
<item> content.

RSS has no reserved field for "when does this event start". By convention,
event-calendar RSS feeds (Localist, The Events Calendar / "the tribe events"
WordPress plugin, and others) reuse the standard <pubDate> element to mean
"this item's event happens at this time", not its original RSS meaning of
"this item was published at this time". That convention is not universal:
while building the fixtures for this adapter we found a real San Jose-area
feed (sanjosejazz.org/events/feed/) whose <pubDate> values are clearly the
WordPress post's last-modified time, not the concert's date -- one item
dated February 2025 sits between two items dated 2026, even though all
three are upcoming shows (see tests/fixtures/sanjosejazz_events.rss.xml and
PREP-NEXT-WEEK.md). There is no reliable way for code to detect that case
from a single feed item, so this adapter does the one thing it safely can:
it trusts <pubDate> exactly as given, and skips any item that has no
parseable date at all, rather than guessing one from the title or
description text. Whether a given feed's <pubDate> actually means "event
start" is a decision for whoever enables that feed as a source in
config.yaml -- see PREP-NEXT-WEEK.md for the one feed we found where the
answer right now is "no, don't enable it yet".
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import feedparser

from ..models import Event, clean_text, infer_categories
from .base import Source

log = logging.getLogger("verdure.sources.rss")


def _coord(entry, key: str):
    v = entry.get(key)
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_rss(raw: str | bytes, source_id: str, default_category: str | None = None,
              organizer_fallback: str = "") -> list[Event]:
    """Parse an RSS 2.0 (or Atom) feed's bytes/text into standard Events.

    Only the feed content passed in is read -- no network call happens here.
    """
    parsed = feedparser.parse(raw)
    events: list[Event] = []

    for entry in parsed.entries:
        title = clean_text(entry.get("title", ""))
        if not title:
            log.debug("Skipping RSS item with no title")
            continue

        # feedparser normalizes a timezone-aware <pubDate> (or Atom
        # <published>) into a UTC time.struct_time. No struct here means the
        # item had no date we can parse -- skip rather than guess one.
        start_struct = entry.get("published_parsed") or entry.get("updated_parsed")
        if not start_struct:
            log.debug("Skipping RSS item with no trustworthy date: %r", title)
            continue
        start = datetime(*start_struct[:6], tzinfo=timezone.utc)

        desc = clean_text(entry.get("summary", "") or entry.get("description", ""))
        link = str(entry.get("link", "") or "").strip()
        guid = str(entry.get("id") or entry.get("guid") or "").strip() or f"{title}-{start.isoformat()}"

        # A feed-provided venue/location field, when one exists (rare --
        # most feeds we found bury location in free-text description, which
        # this adapter does not attempt to parse, for the same
        # "don't guess" reason dates aren't guessed).
        venue_name = clean_text(entry.get("location", "") or entry.get("venue", ""))
        lat = _coord(entry, "geo_lat")
        lon = _coord(entry, "geo_long")

        raw_cats = [str(t.get("term", "")) for t in entry.get("tags", []) if t.get("term")]
        categories = infer_categories(f"{title} {' '.join(raw_cats)}", desc, default_category)

        events.append(Event(
            source_id=source_id,
            source_event_id=guid,
            title=title,
            start=start,
            description=desc,
            venue_name=venue_name,
            lat=lat,
            lon=lon,
            categories=categories,
            organizer=organizer_fallback,
            url=link,
        ))
    return events


class RSSSource(Source):
    def fetch(self) -> list[Event]:
        # Fetch the feed itself only -- item <link> URLs are never requested.
        content = self.http_get(self.cfg["url"]).content
        return parse_rss(
            content,
            source_id=self.id,
            default_category=self.cfg.get("default_category"),
            organizer_fallback=self.name,
        )
