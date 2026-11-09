"""Feed-only event reader. Publication dates require an explicit source opt-in."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

import feedparser
from dateutil.parser import isoparse

from ..models import Event, clean_text, infer_categories, to_float
from .base import Source


def _date(entry, field):
    value = entry.get(field)
    if not value:
        return None
    try:
        dt = isoparse(str(value))
        # A date without a time or timezone does not establish an occurrence time.
        if dt.tzinfo is None or 'T' not in str(value):
            return None
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def parse_rss(raw: str | bytes, source_id: str, default_category: str | None = None,
              organizer_fallback: str = '', *, event_start_field: str | None = None,
              event_end_field: str | None = None,
              published_is_event_start: bool = False) -> list[Event]:
    """Read bytes only; never dereference item URLs.

    Prefer a configured, verified occurrence field. RSS pubDate and Atom
    updated are publication metadata by default. Only enable the pubDate
    override after comparing that feed with official event pages. Never use
    updated as an event date. Untimed/all-day items are omitted here because
    Event has no all-day/unknown-time representation.
    """
    events = []
    # Passing a string URL to feedparser would trigger an unintended request.
    payload = raw.encode('utf-8') if isinstance(raw, str) else raw
    for entry in feedparser.parse(payload).entries:
        title = clean_text(entry.get('title', ''))
        if not title:
            continue
        start = _date(entry, event_start_field) if event_start_field else None
        if not event_start_field and published_is_event_start:
            try:
                published = parsedate_to_datetime(entry.get('published', ''))
                if (published.tzinfo is not None and published.time().isoformat() != '00:00:00'
                        and entry.get('livewhale_all_day') != '1'):
                    start = published.astimezone(timezone.utc)
            except (ValueError, TypeError, OverflowError):
                pass
        if start is None:
            continue
        end = _date(entry, event_end_field) if event_end_field else None
        if end and end < start:
            continue
        link = str(entry.get('link', '')).strip()
        try:
            if urlsplit(link).scheme not in ('http', 'https'):
                link = ''
        except ValueError:
            link = ''
        desc = clean_text(entry.get('summary', '') or entry.get('description', ''))
        coords = entry.get('where', {}).get('coordinates', ())
        lat, lon = to_float(entry.get('geo_lat')), to_float(entry.get('geo_long'))
        if len(coords) == 2:
            lon, lat = to_float(coords[0]), to_float(coords[1])
        cats = ' '.join(str(t.get('term', '')) for t in entry.get('tags', []))
        events.append(Event(
            source_id=source_id,
            source_event_id=str(entry.get('id') or entry.get('guid') or f'{link}|{start.isoformat()}'),
            title=title, start=start, end=end, description=desc,
            venue_name=clean_text(entry.get('location') or entry.get('venue') or
                                  entry.get('georss_featurename') or ''),
            lat=lat, lon=lon,
            categories=infer_categories(title + ' ' + cats, desc, default_category),
            organizer=organizer_fallback, url=link,
        ))
    return events


class RSSSource(Source):
    def fetch(self) -> list[Event]:
        content = self.http_get(self.cfg['url']).content
        return parse_rss(
            content, source_id=self.id,
            default_category=self.cfg.get('default_category'), organizer_fallback=self.name,
            event_start_field=self.cfg.get('event_start_field'),
            event_end_field=self.cfg.get('event_end_field'),
            published_is_event_start=self.cfg.get('published_is_event_start') is True,
        )
