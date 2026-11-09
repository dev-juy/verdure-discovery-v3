import gzip
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from verdure.sources.rss import RSSSource, parse_rss

FIXTURES = Path(__file__).parent / 'fixtures' / 'raw'


def test_real_sjsu_feed_is_opt_in():
    raw = gzip.decompress((FIXTURES / 'sjsu.xml.gz').read_bytes())
    assert parse_rss(raw, 'sjsu') == []
    events = parse_rss(raw, 'sjsu', published_is_event_start=True)
    event = next(e for e in events if 'esports-and-gaming-showcase-fall-2026' in e.url)
    assert event.start == datetime(2026, 11, 9, 18, 30, tzinfo=timezone.utc)
    assert any(e.lat is not None for e in events)


def test_real_scu_feed_reads_location_and_skips_all_day():
    events = parse_rss(gzip.decompress((FIXTURES / 'scu.xml.gz').read_bytes()), 'scu', published_is_event_start=True)
    event = next(e for e in events if '521944' in e.url)
    assert event.start == datetime(2026, 11, 10, 0, 30, tzinfo=timezone.utc)
    assert event.venue_name
    assert all('521345-confronting' not in e.url for e in events)


def test_real_grassroots_feed_rejects_publication_dates():
    raw = gzip.decompress((FIXTURES / 'grassroots.xml.gz').read_bytes())
    assert parse_rss(raw, 'grassroots') == []


def test_explicit_occurrence_field_and_no_date_guessing():
    raw = '''<rss xmlns:ev="urn:events"><channel>
    <item><title>Valid</title><ev:start>2026-11-14T10:00:00-08:00</ev:start>
    <ev:end>2026-11-14T12:00:00-08:00</ev:end><location>Garden</location></item>
    <item><title>No event time</title><pubDate>Fri, 13 Nov 2026 10:00:00 GMT</pubDate></item>
    <item><title>Ambiguous timezone</title><ev:start>2026-11-14T10:00:00</ev:start></item>
    <item><title>Invalid date</title><ev:start>not a date</ev:start></item>
    <item><title>Backwards</title><ev:start>2026-11-14T10:00:00-08:00</ev:start>
    <ev:end>2026-11-13T10:00:00-08:00</ev:end></item>
    </channel></rss>'''
    events = parse_rss(raw, 'x', event_start_field='ev_start', event_end_field='ev_end')
    assert len(events) == 1
    assert events[0].venue_name == 'Garden'
    assert events[0].end - events[0].start == __import__('datetime').timedelta(hours=2)


def test_fetch_reads_only_feed(monkeypatch):
    source = RSSSource({'id': 'x', 'url': 'https://example.org/events.rss',
                        'published_is_event_start': True})
    requests = []
    def get(url):
        requests.append(url)
        return SimpleNamespace(content=b'<rss><channel><item><title>Event</title><link>https://example.org/detail</link><pubDate>Sat, 14 Nov 2026 18:00:00 GMT</pubDate></item></channel></rss>')
    monkeypatch.setattr(source, 'http_get', get)
    assert len(source.fetch()) == 1
    assert requests == ['https://example.org/events.rss']
