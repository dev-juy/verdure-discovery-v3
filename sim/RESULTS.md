# Ranking comparison simulation

Seed: 20261108; 1,000 trials per configuration. Fixed-horizon decision: B wins when its credited engagements exceed A; ties remain undecided.

An edge of 55% means B receives 55% of informative engagements. Each session produces at most ONE independent credited signal. Taps, saves and RSVPs from one user are not counted as independent sessions.

| Engagement rate | B preference | Sessions | Correct B | Incorrect A | Tie |
| --- | --- | --- | --- | --- | --- |
| 100% | 52% | 100 | 61.2% | 30.6% | 8.2% |
| 100% | 52% | 300 | 69.8% | 26.4% | 3.8% |
| 100% | 52% | 1,000 | 86.9% | 11.3% | 1.8% |
| 100% | 55% | 100 | 81.7% | 12.4% | 5.9% |
| 100% | 55% | 300 | 94.8% | 4.3% | 0.9% |
| 100% | 55% | 1,000 | 100.0% | 0.0% | 0.0% |
| 100% | 60% | 100 | 98.1% | 1.4% | 0.5% |
| 100% | 60% | 300 | 100.0% | 0.0% | 0.0% |
| 100% | 60% | 1,000 | 100.0% | 0.0% | 0.0% |
| 25% | 52% | 100 | 57.6% | 35.7% | 6.7% |
| 25% | 52% | 300 | 64.1% | 32.8% | 3.1% |
| 25% | 52% | 1,000 | 73.8% | 24.5% | 1.7% |
| 25% | 55% | 100 | 66.7% | 27.1% | 6.2% |
| 25% | 55% | 300 | 76.9% | 19.3% | 3.8% |
| 25% | 55% | 1,000 | 93.4% | 6.2% | 0.4% |
| 25% | 60% | 100 | 83.4% | 12.7% | 3.9% |
| 25% | 60% | 300 | 96.0% | 3.4% | 0.6% |
| 25% | 60% | 1,000 | 100.0% | 0.0% | 0.0% |

## Recommendation

**1,000 informative sessions** as the initial planning target for a 55% edge. This is the largest tested count, not a guarantee for a 52% edge. With a 25% informative engagement rate, plan for about 4,000 total sessions to obtain 1,000 informative ones.

At a 55% edge and 100% engagement, 300 sessions picked B in 94.8% of trials. The earlier multi-signal simulation overstated evidence per session.

This table measures how often a forced directional choice is correct; it is NOT 95% statistical significance or 80% power for a hypothesis test. The worst Monte Carlo standard error with 1,000 trials is about 1.6 percentage points.

The accompanying team-draft function creates balanced, duplicate-free feeds and records ownership. The sizing model starts AFTER attribution and uses a calibrated conditional B preference; it does not claim that arbitrary rankings inherently yield that preference. Identical rankings should be excluded from the informative sample.

Before shipping: choose one primary outcome, randomize draft order, cluster by user, measure no-action sessions and position bias, and precommit the stopping rule. No production conversion or correlation data was supplied.

Reproduce: `python sim/interleaving_sim.py`
