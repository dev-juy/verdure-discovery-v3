# Actual feed snapshots

These gzip-compressed XML files preserve complete response bytes fetched from the URLs in `PROVENANCE.json` on 2026-11-08. Decompress with gzip before parsing; SHA-256 and byte counts refer to the original uncompressed response bytes. Compression is lossless. They replace the old reconstructed/transcribed fixtures, which were removed.

- **SJSU Localist:** event `pubDate` was compared with the official Esports and Gaming Showcase page (2026-11-09 10:30 Pacific = 18:30 UTC). Opt-in is required; default parsing rejects it.
- **SCU LiveWhale:** event `pubDate` was compared with the official Art Hazelwood event (2026-11-09 16:30 Pacific = 2026-11-10 00:30 UTC). Location is supplied by the feed; `livewhale:all_day=1` is excluded.
- **Grassroots Ecology:** `pubDate` is publication metadata rather than the listed event occurrence. Default parsing returns no events. Use advertised event ICS links instead.

A feed-level opt-in is a source contract, not a parser heuristic. Do not apply it to a new feed merely because it contains parseable dates. Full feed fixtures may include records outside the benchmark window; they are test inputs, not the benchmark.
