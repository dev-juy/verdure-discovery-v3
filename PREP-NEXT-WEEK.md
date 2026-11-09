# Verdure weekly-task handoff — November 9, 2026

**Overall status: not 100% complete.** The code and replacement benchmark are ready for review. The original 100-row accuracy-audit sample is missing, and the brief requires John's personal link checks, which an assistant cannot truthfully mark complete.

Work stays on `prep-next-week` in `dev-juy/verdure-discovery-v3`, building on the existing prep branch. The requested original base is `v3` at `0ab11e6`; neither `main` nor `v3` is changed. The newer November 9–22 benchmark supersedes the old October 20–November 2 coverage window. The historical `data/coverage-test-set.csv` is retained as an older artifact, not current evidence.

## Replacement discovery benchmark

`data/verdure-benchmark-2026-11-09_22.csv` contains **120 event occurrences**, checked against public official pages on November 8:

| Audience | Events |
| --- | ---: |
| Families and kids | 20 |
| Students | 20 |
| Young adults | 20 |
| Outdoors and volunteering | 20 |
| Hidden gems | 40 |

The dataset covers **42 website sources**, with **at most five rows per site**, and **29 occurrences in Gilroy/Morgan Hill/Milpitas/Santa Clara/Cupertino collectively** (the threshold is collective, not a quota for every city). Distinct library tenants count as separate websites. Some event pages use organizer-owned ticketing/calendar providers. Sources are official organizers, venues, libraries, campuses, or the Downtown Campbell Business Association's calendar; no prohibited social/event aggregators are included.

All times use explicit Pacific UTC offsets. **26 end times are blank** because the checked page did not establish an exact end. Trail meeting directions or official GPS coordinates stand in for street numbers where the organizer uses those. Campus rows retain the named room/building in `venue`; campus addresses do not imply a precise room entrance. Repeated markets, worship services and trivia nights are separately dated occurrences, not duplicate rows. Audience labels are editorial categories, not proof that admission is unrestricted; confirm age, registration, campus affiliation, fees and availability on the official page.

**Verification limits:** these are assistant-checked event facts, not John's personal sign-off or a guarantee against future cancellation. `checked_on` records the assistant's page checks. `data/benchmark-human-review.csv` has blank reviewer/date/correction columns for the required personal review. `data/benchmark-validation.json` records reproducible structural checks and explicitly leaves human review false. Unknown ends and any corrections should be settled during that review. Blank `terms_ok` follows the brief and does not claim permission or legal clearance. Sites that returned access blocks were skipped; no blocked registration portal was used as evidence for event details available on the organizer's public page.

`data/benchmark-sources-and-feeds.csv` lists every source and the actual feed links found. Blank feeds mean no event feed was identified on the checked pages. Advertised per-event ICS links are distinguished from RSS downloads; their individual transports were not all tested. No new source was enabled automatically.

## RSS reader and offline tests

`verdure/sources/rss.py` remains registered as `type: rss`. It returns the existing `Event` shape and only fetches the configured feed, never item links. String payloads become bytes before parsing, preventing feedparser from treating them as URLs.

Publication dates are rejected by default. Set `event_start_field` (and optionally `event_end_field`) to a verified namespaced field as feedparser exposes it, e.g. `ev_start`; it must contain an ISO timestamp with timezone. Only for a verified source contract may `published_is_event_start: true` opt into RSS `pubDate`. There is no `updated` fallback. Untimed/all-day entries are skipped because the current `Event` shape cannot preserve their semantics; missing ends remain unknown. Invalid or backwards dates are not invented.

`tests/fixtures/raw/` contains three actual full local feed downloads (losslessly gzip-compressed): SJSU, SCU and Grassroots Ecology. Their URLs, exact hashes, dates and byte counts are recorded. SJSU/SCU occurrence semantics were checked against official event pages; Grassroots publication dates are deliberately rejected. Old transcribed fixtures were removed. `tests/test_rss.py` exercises real snapshots, missing/untrustworthy dates, explicit date fields, all-day exclusion and the no-item-page-fetch contract.

## Geographic points

`data/neighborhoods.json` contains 10 named areas. Five neighborhood interior points derive from official City of San Jose GIS polygons; four city internal points come from Census TIGERweb. SJSU uses an explicitly labeled official campus anchor. These are useful area-selection points, not parcel or neighborhood centroids. Required features from the official GIS responses are in `data/geo_provenance/`; `scripts/rebuild_neighborhoods.py` reproduces them offline. Existing region settings still use downtown San Jose (37.3382, -121.8863); the named points satisfy the older 25-mile radius check.

## Ranking comparison simulation

`sim/interleaving_sim.py` and `sim/RESULTS.md` provide the requested 52%/55%/60% preferences, 100/300/1,000 sessions and 1,000 trials per configuration, with deterministic seed 20261108. A 25% informative-engagement sensitivity is also reported. The team-draft helper handles duplicates and exhausted rankings. The sizing model starts **after attribution**, at most one independent engagement per session; it is explicitly not a production power calculation.

**Recommendation:** plan for **1,000 informative sessions for a 55% preference**; at 25% engagement that means roughly 4,000 total sessions. At a 52% preference, 300 informative sessions selected B in only 69.8% of trials. The older conclusion that 300 sessions reliably resolves a small edge was too optimistic. Directional correctness in this model is not statistical significance.

## Organizer messages

`data/fix_it_messages.json` covers all seven blocking reasons, each under 15 words. A test checks exact reason coverage and the word limit.

## Missing audit and remaining sign-off

Read `data/ACCURACY-AUDIT-STATUS.md`. The original `verdure-accuracy-audit-sample.csv` must be supplied to inspect the required 100 rows and produce real field-error counts, source usefulness means and a genuine filler example. An empty template is provided; no audit statistics were fabricated. John must also personally review the replacement benchmark as requested in the brief. Those are the two outstanding completion gates.

## Reproduce checks

```bash
pip install -r requirements.txt
python -m pytest -q
python scripts/validate_benchmark.py
python scripts/rebuild_neighborhoods.py
python sim/interleaving_sim.py
```

The test suite passed **25 tests**. Benchmark structural validation returned zero errors. These checks are offline and do not claim that the benchmark was discovered by the live engine or that every organizer feed works in production. No paid services or new secrets are required.

## Delivery verification — November 9

Re-ran the full offline suite: 25 passed. Benchmark validator reports zero structural errors. The original audit sample remains unavailable after another exact-title file search and email search. Personal benchmark review remains outstanding. Neither is represented as completed.
