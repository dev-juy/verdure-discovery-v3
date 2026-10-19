# Interleaving simulation results

Team-draft interleaving simulation, seed `20261019`, 1000 trials per (edge, sessions) pair. Run `python sim/interleaving_sim.py` to reproduce (numbers move by a point or two on a different seed, not more).

| Edge | Sessions | B correctly declared winner | A wrongly declared winner | Tie (no winner) |
| --- | --- | --- | --- | --- |
| 52% | 100 | 77.9% | 20.0% | 2.1% |
| 52% | 300 | 91.7% | 7.3% | 1.0% |
| 52% | 1000 | 99.5% | 0.5% | 0.0% |
| 55% | 100 | 97.4% | 2.1% | 0.5% |
| 55% | 300 | 99.9% | 0.1% | 0.0% |
| 55% | 1000 | 100.0% | 0.0% | 0.0% |
| 60% | 100 | 100.0% | 0.0% | 0.0% |
| 60% | 300 | 100.0% | 0.0% | 0.0% |
| 60% | 1000 | 100.0% | 0.0% | 0.0% |

## Recommendation

**300 sessions** is the smallest of the three tested counts that correctly picks B as the winner at least 90% of the time across all three edges tested (worst case 92%, at the toughest 52% edge; best case 100%, at the 60% edge).

The sprint's guess of 300 sessions holds up well for a clear edge (55-60%), but is noticeably weaker right at a 52% edge -- see the table. If the two rankings being compared are expected to be close (a small tweak, not a rebuild), lean toward 1,000 sessions before trusting a declared winner; 300 is fine once a test is running for a visibly larger edge.

Caveats this simulation does not model: click-position decay within a session, graded (vs. binary) relevance, and users who see a session but engage with nothing. All three would make real signal noisier than this model's, so treat these numbers as an upper bound on how fast the sprint's test can actually converge.
