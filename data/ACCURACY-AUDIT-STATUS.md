# Accuracy audit — blocked on the supplied sample

The brief calls for **Rishit's existing 100-row `verdure-accuracy-audit-sample.csv`**, covering October 29–November 14 across six sources. That file was not supplied and was not found in the connected files or repository. The new benchmark is a separate deliverable and cannot substitute for that sample.

## Required five-line summary

Rows audited: **0 of the required 100**; input sample missing.

1. Fully correct rows: **not measured / 100**.
2. Mistakes by type: **not measured**, not zero.
3. Mean usefulness for each of the six sources: **not measured**.
4. Low-value event types with example row numbers: **not identified without the sample**.
5. Five highest-impact fixes from the sample: **not determined**; independent engineering fixes are listed below.

`accuracy-audit-template.csv` is an empty review schema, not completed audit results. Score usefulness 1 = filler, 2 = fine for the right person, 3 = worth planning a day around. Record every wrong field, including price, cancellation and duplicate references.

## Five engineering fixes identified independently

These are supported by code/benchmark work, **not findings from the missing sample**:

1. Reject RSS publication dates by default; require verified event-date fields or explicit source opt-in. Implemented and tested.
2. Preserve unknown end times and distinguish all-day/unknown-time events instead of inventing times. Benchmark preserves blanks; RSS skips unrepresentable untimed items. A full all-day model remains outside this task.
3. Use official GIS/Census area points with reproducible provenance. Implemented.
4. Count at most one independent signal per session in ranking-test sizing; report no-action sensitivity. Implemented.
5. Require occurrence-level duplicate checks and explicit audience/source/date quotas before accepting a benchmark. Implemented structural validator; personal review remains outstanding.
