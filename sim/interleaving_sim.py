"""Idealized sizing model: one independently credited engagement per session.

B preference is conditional on an informative engagement. Sessions without an
engagement contribute zero. This is not a production power calculation: no
position effects, repeated users, or correlated taps/saves/RSVPs are modeled.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

EDGES = (0.52, 0.55, 0.60)
SESSION_COUNTS = (100, 300, 1000)
TRIALS_PER_CONFIG = 1000
SEED = 20261108


def team_draft_interleave(a, b, k, rng):
    """Balanced random team drafting; remove duplicates, record slot ownership."""
    ranks = {'A': list(dict.fromkeys(a)), 'B': list(dict.fromkeys(b))}
    picks = {'A': 0, 'B': 0}
    seen, feed, credit = set(), [], {}
    while len(feed) < k:
        available = {t: next((x for x in ranks[t] if x not in seen), None) for t in ranks}
        teams = [t for t in ranks if available[t] is not None]
        if not teams:
            break
        minimum = min(picks[t] for t in teams)
        team = rng.choice([t for t in teams if picks[t] == minimum])
        item = available[team]
        seen.add(item)
        feed.append(item)
        credit[item] = team
        picks[team] += 1
    return feed, credit


def simulate_trial(n, edge, rng, engagement_rate=1.0):
    score = 0
    for _ in range(n):
        if rng.random() < engagement_rate:
            score += 1 if rng.random() < edge else -1
    return 'B' if score > 0 else 'A' if score < 0 else 'tie'


def simulate(seed=SEED, trials=TRIALS_PER_CONFIG):
    rng = random.Random(seed)
    rows = []
    for engagement_rate in (1.0, 0.25):
        for edge in EDGES:
            for sessions in SESSION_COUNTS:
                outcomes = [simulate_trial(sessions, edge, rng, engagement_rate) for _ in range(trials)]
                rows.append((engagement_rate, edge, sessions,
                             outcomes.count('B') / trials, outcomes.count('A') / trials,
                             outcomes.count('tie') / trials))
    return rows


def write_results(rows, output, seed, trials):
    lines = ['# Ranking comparison simulation', '',
        f'Seed: {seed}; {trials:,} trials per configuration. Fixed-horizon decision: B wins when its credited engagements exceed A; ties remain undecided.', '',
        'An edge of 55% means B receives 55% of informative engagements. Each session produces at most ONE independent credited signal. Taps, saves and RSVPs from one user are not counted as independent sessions.', '',
        '| Engagement rate | B preference | Sessions | Correct B | Incorrect A | Tie |',
        '| --- | --- | --- | --- | --- | --- |']
    for rate, edge, n, correct, wrong, tie in rows:
        lines.append(f'| {rate:.0%} | {edge:.0%} | {n:,} | {correct:.1%} | {wrong:.1%} | {tie:.1%} |')
    baseline = [r for r in rows if r[0] == 1 and r[1] == .55 and r[2] == 300][0]
    lines += ['', '## Recommendation', '',
        '**1,000 informative sessions** as the initial planning target for a 55% edge. This is the largest tested count, not a guarantee for a 52% edge. With a 25% informative engagement rate, plan for about 4,000 total sessions to obtain 1,000 informative ones.', '',
        f'At a 55% edge and 100% engagement, 300 sessions picked B in {baseline[3]:.1%} of trials. The earlier multi-signal simulation overstated evidence per session.', '',
        'This table measures how often a forced directional choice is correct; it is NOT 95% statistical significance or 80% power for a hypothesis test. The worst Monte Carlo standard error with 1,000 trials is about 1.6 percentage points.', '',
        'The accompanying team-draft function creates balanced, duplicate-free feeds and records ownership. The sizing model starts AFTER attribution and uses a calibrated conditional B preference; it does not claim that arbitrary rankings inherently yield that preference. Identical rankings should be excluded from the informative sample.', '',
        'Before shipping: choose one primary outcome, randomize draft order, cluster by user, measure no-action sessions and position bias, and precommit the stopping rule. No production conversion or correlation data was supplied.', '',
        'Reproduce: `python sim/interleaving_sim.py`', '']
    Path(output).write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=SEED)
    parser.add_argument('--trials', type=int, default=TRIALS_PER_CONFIG)
    parser.add_argument('--output', default='sim/RESULTS.md')
    args = parser.parse_args()
    if args.trials < 1:
        parser.error('--trials must be positive')
    rows = simulate(args.seed, args.trials)
    write_results(rows, args.output, args.seed, args.trials)
    for row in rows:
        print(row)


if __name__ == '__main__':
    main()
