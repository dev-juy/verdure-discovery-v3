"""Offline structural checks; these do not establish page truth or human review."""
import csv
import json
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ['title', 'start', 'end', 'venue', 'address', 'official_url', 'source_site',
          'group', 'checked_on', 'feed_url', 'terms_ok']
TARGETS = {'Families and kids': 20, 'Students': 20, 'Young adults': 20,
           'Outdoors and volunteering': 20, 'Hidden gems': 40}
BANNED = ('facebook.com', 'instagram.com', 'meetup.com', 'eventbrite.com', 'active.com', 'maps.google.com', 'maps.app.goo.gl')


def inspect(rows):
    errors = []
    groups = Counter(r['group'] for r in rows)
    sites = Counter(r['source_site'] for r in rows)
    seen, regional = set(), 0
    for i, r in enumerate(rows, 2):
        if set(r) != set(FIELDS): errors.append(f'Line {i}: wrong columns')
        for f in ['title', 'start', 'venue', 'address', 'official_url', 'source_site', 'group', 'checked_on']:
            if not r[f].strip(): errors.append(f'Line {i}: empty {f}')
        start = datetime.fromisoformat(r['start'])
        if start.tzinfo is None or not date(2026, 11, 9) <= start.astimezone(ZoneInfo('America/Los_Angeles')).date() <= date(2026, 11, 22):
            errors.append(f'Line {i}: date/time outside benchmark window or missing timezone')
        if r['end']:
            end = datetime.fromisoformat(r['end'])
            if end.tzinfo is None or end < start: errors.append(f'Line {i}: invalid end')
        key = (r['title'].casefold().strip(), start.isoformat(), r['venue'].casefold().strip())
        if key in seen: errors.append(f'Line {i}: duplicate occurrence')
        seen.add(key)
        host = urlsplit(r['official_url']).hostname or ''
        if host.removeprefix('www.') != r['source_site']: errors.append(f'Line {i}: source mismatch')
        if any(host == b or host.endswith('.' + b) for b in BANNED): errors.append(f'Line {i}: disallowed source')
        if r['terms_ok'] not in ('', 'N'): errors.append(f'Line {i}: terms flag must be blank or N')
        if r['terms_ok'] == 'N': errors.append(f'Line {i}: forbidden source retained')
        date.fromisoformat(r['checked_on'])
        regional += any(city in r['address'].lower() for city in ('gilroy', 'morgan hill', 'milpitas', 'santa clara', 'cupertino'))
    if len(rows) != 120: errors.append(f'Expected 120 rows, got {len(rows)}')
    if groups != Counter(TARGETS): errors.append(f'Wrong audience totals: {dict(groups)}')
    if len(sites) < 40: errors.append(f'Only {len(sites)} website sources')
    if max(sites.values(), default=0) > 5: errors.append('A website contributes more than five rows')
    if regional < 15: errors.append(f'Only {regional} target-city events')
    return dict(rows=len(rows), groups=dict(groups), distinct_websites=len(sites),
                max_rows_per_website=max(sites.values(), default=0), target_city_events=regional,
                missing_end_times=sum(not r['end'] for r in rows), structural_errors=errors,
                human_review_completed=False, audit_completed=False)


if __name__ == '__main__':
    with (ROOT / 'data/verdure-benchmark-2026-11-09_22.csv').open(newline='', encoding='utf-8') as f:
        result = inspect(list(csv.DictReader(f)))
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['structural_errors']))
