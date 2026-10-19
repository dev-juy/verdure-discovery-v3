# Prep-next-week handoff

Everything in this doc was built on the `prep-next-week` branch, off `v3`
at commit `0ab11e6`. `main` and `v3` were not touched. Four days of prep
work, done Oct 19, 2026, for the developers' sprint starting next week.

## 1. `data/coverage-test-set.csv` — 100-event coverage test set

**What it is:** 100 real, upcoming events within 25 miles of downtown San
José (37.3382, -121.8863), each hand-checked against the organization's own
public official page (no login required), none sourced from
Instagram/Facebook/Meetup/Eventbrite/ACTIVE.com. All start between
2026-10-20 and 2026-11-02. 25 events in each of the four audience groups
(Families and kids / Students / Young adults / Outdoors and volunteering),
spread across 23 different website domains, with no domain contributing
more than 10 of the 100 rows (`events.sjsu.edu` is at the cap, exactly 10 —
8 from Students, 2 from Young adults).

**How to run the coverage test next week:** run Verdure's discovery against
this same 14-day window and check how many of these 100 `official_url`s (or
their underlying event) its sources actually surfaced. Every miss is a
specific, checkable gap: either a missing source (no adapter for that
site yet) or a source that's enabled but didn't catch that particular
event (wrong date window, pagination, JS-rendered content the adapter
can't see, etc.).

**How it was actually built, and what that means for you:**

This sandbox's outbound network only reaches package registries and
GitHub — no browsing arbitrary sites by curl/requests. So this wasn't built
by running Verdure's own adapters against live feeds; it was built by using
this session's own web-search and web-fetch tools to find each event,
open its official page, and copy down the title/date/time/venue/address
shown there. Every row's `official_url` is the exact page that was opened
to confirm it, and `checked_on` is 2026-10-19 for all 100 rows (built in
one sitting).

Two consequences worth knowing before you lean on this file:

- **Spot-check a sample before trusting it at scale.** This was hand
  verification by an AI session reading pages, not a human clicking
  through 100 links one at a time with a calendar in hand. The
  instructions this file was built from called for exactly that kind of
  one-by-one human check; that didn't happen here. Before the coverage
  run, someone should re-open a random 10-15 of the 100 `official_url`s
  and confirm the date/time/venue still match — treat this file as a
  strong first draft of the test set, not a guaranteed-clean one.
- **A few sites that looked promising turned out not to work and are
  *not* represented in the 100,** so don't read their absence as "nothing
  interesting happens there" — it means the listing couldn't be verified
  this round:
  - **Santa Clara University (scu.edu)** — pages returned repeated server
    errors; the one calendar view that loaded had no venue info.
  - **San José City College, Evergreen Valley College, Mission College** —
    calendars are JS-rendered; direct fetch returned empty shells.
  - **De Anza's own `calendar.deanza.edu` (Localist)** — blocked by
    robots.txt; used `cis.deanza.edu/events/` instead (same campus).
  - **SAP Center** — no concerts in the Oct 20–Nov 2 window (hockey only).
  - **San José Jazz's venue calendar, Santana Row's own calendar, Café
    Stritch** — no separately-hosted, fetchable calendar with confirmable
    dates in-window.
  - **Winchester Mystery House's 2026 Halloween event dates** — not yet
    published on an officially fetchable page as of 2026-10-19.
  - **Santa Clara County Parks, City of San José Parks & Rec, Valley
    Water, SCVAS/Santa Clara Valley Bird Alliance, Sierra Club Loma
    Prieta** — calendars either had nothing dated in-window, were
    JS-dependent pages that never rendered real events, or only surfaced
    events through Eventbrite/Meetup/Idealist (excluded by the rules).
    The "Outdoors and volunteering" 25 instead comes from
    openspace.org, grpg.org (Guadalupe River Park Conservancy),
    grassrootsecology.org, openspacetrust.org, and cnps-scv.org — none
    of which were in the original suggested list, but all are real,
    public, and within the region.
  - A couple of rows share one `official_url` across multiple distinct
    event titles where the only live, fetchable page was a venue's
    general events listing rather than a one-event-per-page permalink
    (`openspace.org`'s guided-activities listing, and
    `events.sjsu.edu/department/hammer_theatre` for two Hammer Theatre
    shows). Everything else has a one-event permalink.
  - One real duplicate was caught and fixed during assembly: "CLA
    Presents Barbara Kingsolver Receiving the Steinbeck Award" was
    independently found for both the Students and Young Adults groups.
    It's kept once (under Students); Young Adults' 25th slot is a second,
    separately-dated occurrence of the Downtown Campbell farmers' market
    (Nov 1, distinct from the Oct 25 occurrence already in the set).

If any of this leaves a group short of real options once you look closer,
re-read the task's own instruction: cut the simulation before the
neighborhood list, and never cut this file below 100.

## 2. `verdure/sources/rss.py` — RSS event reader

Plain RSS 2.0 adapter, registered as `type: rss` in `verdure/sources/__init__.py`
and `REGISTRY`. Reads title, start time, location (when the feed provides
one), link, and description from each item; never fetches the pages an
item's `<link>` points to. Full design rationale is in the module's own
docstring — the short version:

RSS has no reserved "event start" field. Event-calendar feeds conventionally
reuse `<pubDate>` to mean that, but it isn't universal. While building the
three test fixtures (`tests/fixtures/*.rss.xml`, each a real San José-area
feed verified live on 2026-10-19 and transcribed here since this sandbox
can't curl them directly — see the comment at the top of each fixture), we
found a real example where it's wrong: **`sanjosejazz.org/events/feed/`'s
`<pubDate>` is the WordPress post's last-modified time, not the show's
date** (one item dated Feb 2025 sits between two items dated 2026, all
three listed as upcoming). There's no way for code to detect that from a
single item, so the adapter trusts `<pubDate>` as given and only skips
items with no parseable date at all. **Don't enable `sanjosejazz.org`'s RSS
feed as a live source** until/unless that's fixed on their end or a
different trustworthy field is found — doing so now would feed it wrong
dates silently.

The other two fixtures (`events.sjsu.edu/calendar.xml` — Localist, and
`cdm.org/events/feed/` — WordPress "The Events Calendar") both have a
`<pubDate>` that really is the event's start time, confirmed by the dates
running forward in order from the day they were fetched.

Tests: `test_rss_parses_sjsu_calendar_feed`, `test_rss_parses_cdm_events_feed`,
`test_rss_skips_item_with_no_trustworthy_date` in `tests/test_engine.py`.

## 3. `data/neighborhoods.json` — verified neighborhood list

Replaces the old estimated coordinates in `verdure/geo.py`'s `AREAS` table.
`verdure/geo.py` now has `load_areas()`, which reads this file and falls
back to a small built-in table (same "bad/missing data degrades, never
crashes" rule as the rest of the engine) if it's missing or unreadable.

Each of the 10 areas is anchored to a real official address rather than an
estimate of the neighborhood's center — an SJPL branch library, a city
hall, or (for "sjsu" and "cambrian", which aren't official neighborhood
names) the campus address or the nearest official city facility, same
treatment the task description calls for. `confirmed_live: true` means this
session's fetch tool successfully re-loaded that address from the official
site on 2026-10-19; `false` means the fetch errored on retry but the
address itself is the well-established public one for that building —
worth one more quick check, not a guess. See each entry's `source` and
`note` fields for specifics.

Coordinates are accurate to roughly a city block (the anchor address's
location), not a GIS parcel centroid — there was no way to query
data.sanjoseca.gov's actual GIS layers from this sandbox. If you need
tighter precision, cross-check against that portal directly.

Test: `test_neighborhoods_are_within_region_radius` confirms every area is
within 25 miles of downtown San José.

## 4. `sim/interleaving_sim.py` + `sim/RESULTS.md` — ranking A/B test sizing

Simulates team-draft interleaving (the real algorithm, implemented in
`team_draft_interleave()`) to test the sprint's guess that 300 sessions is
enough to pick a winning ranking. Tested at a 52%, 55%, and 60% edge, 1000
trials each at 100/300/1000 sessions.

**Result: 300 sessions is a reasonable floor, but shaky right at the
toughest 52% edge** (picks the true winner ~92% of the time there, vs.
~100% at 55-60%). Full table and the reasoning behind the recommendation
are in `sim/RESULTS.md` — reproduce with `python sim/interleaving_sim.py`.
The simulation's own caveats (no click-position decay, no graded relevance,
one engagement signal per contested round) are documented at the top of the
script; treat its numbers as an upper bound on how fast a real test
converges, not a guarantee.

## 5. `data/fix_it_messages.json` — organizer fix-it messages

One message per rejection reason in `verdure/validate.py`'s `BLOCKING` set
— all 7 covered, each under 15 words, no blame.

## 6. What's genuinely unfinished / needs a second look

- **Coverage test set:** spot-check a random sample before the actual
  coverage run (see section 1) — this was AI-verified, not human-verified
  the way the brief asked for.
- **`sanjosejazz.org`'s RSS feed should not be enabled** as a live source
  until its `<pubDate>` semantics are fixed or a better field is found
  (see section 2).
- **Four `data/neighborhoods.json` entries** (`downtown san jose`,
  `cambrian`, `santa clara`, `campbell`) use addresses that are
  well-established but weren't successfully re-confirmed via a live fetch
  this session (the fetch errored on retry, not the address) — worth one
  more check against the source links in the file.
- **BiblioCommons adapters** for San José Public Library / Santa Clara
  County Library are still not implemented — same as before this week's
  prep; the RSS adapter added this week is not a replacement for them
  (bibliocommons.com doesn't appear to expose a public RSS feed; the
  coverage test set's library rows were found via their event pages
  directly, not a feed).
- **Organizer age ranges** are still not collected anywhere, so missing
  age data still passes every child-age filter by default — unchanged
  from before, flagging again since it's the main remaining gap in
  child-safety filtering.
- **The live SJSU/SCU/Ticketmaster feeds still haven't been run against
  the real engine** from a machine with normal internet access — this
  sandbox can search and fetch individual pages with its own tools, but
  `run.py`'s own adapters (plain `requests` calls) are blocked by this
  sandbox's egress proxy the same way they always have been. That's still
  the top "next step" before trusting any of this against the live
  pipeline rather than against hand-checked pages.

## 7. Running everything

```bash
pip install -r requirements.txt
python -m pytest -q          # 19 passed
python sim/interleaving_sim.py   # regenerates sim/RESULTS.md
```

No new environment variables or paid services were introduced — the RSS
adapter uses the same `requests`-based `Source.http_get()` every other
adapter uses, and `feedparser` (added to `requirements.txt`) is free and
open source like everything else already in this project.
