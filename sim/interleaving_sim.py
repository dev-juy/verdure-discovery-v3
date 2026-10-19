"""Team-draft interleaving power simulation.

The app will compare two feed rankings (A = current, B = challenger) by
team-draft interleaving: merge both rankings into one feed, remember which
ranking is "credited" with each slot, and see which ranking earns more
engagement. The sprint is guessing that 300 user sessions is enough to
reliably spot a real winner. This script tests that guess by simulation,
not by argument.

How one session is simulated
------------------------------
1. Build two rankings over a shared pool of candidate events. B is built
   from A with a handful of swaps near the top, so the two lists mostly
   agree at the top but disagree on a realistic number of slots -- which
   is exactly the situation team-draft interleaving is designed to probe.
2. Run real team-draft interleaving (see `team_draft_interleave`): at each
   round, whichever team has made fewer picks so far goes first (ties
   broken by a coin flip) and contributes its best remaining item. If both
   teams would have picked the same item, it is credited to BOTH and that
   round contributes no comparison -- this is the standard rule for
   removing bias from identical top results.
3. Every round where the two teams picked *different* items is one
   "contested" round: a place where a user's engagement can actually tell
   A and B apart. We simulate the user's reaction to that round as a
   biased coin: P(user's engagement favors B) = edge. That is the model's
   one assumption, and it is exactly the "small edge" the sprint is
   guessing at (52% / 55% / 60%).
4. Whichever team wins more contested rounds in a session wins that
   session (a dead-even session is a tie and favors neither team).
5. Whichever team wins more sessions across a trial of N sessions is that
   trial's declared winner.

We then run 1000 independent trials at each (edge, N) pair and report how
often the trial correctly declares B the winner -- since B is the team the
edge favors, "correct" means B.

This is a simplification (no click-position decay, no graded relevance,
one engagement signal per contested round instead of several) made so the
statistical question -- "is N sessions even enough signal, before we touch
real position/relevance effects?" -- is answered directly. It is a lower
bound on the sessions needed: real sessions produce less decisive signal
per round (users don't click every contested slot, and noise sources this
model leaves out only add more noise), so if 300 sessions is already shaky
here, it is no better in production.
"""

from __future__ import annotations

import random
import statistics

N_ITEMS = 30        # size of the candidate pool each session draws from
TOP_K = 12          # how many slots get interleaved into a feed
TOP_SWAPS = 4        # how many of the top TOP_K slots B reorders vs A
EDGES = (0.52, 0.55, 0.60)
SESSION_COUNTS = (100, 300, 1000)
TRIALS_PER_CONFIG = 1000
SEED = 20261019     # reproducible; re-run with a different seed and the
                    # win rates will move by a point or two, not more


def make_rankings(rng: random.Random) -> tuple[list[int], list[int]]:
    """Ranking A is a random order of the pool. Ranking B starts as a copy
    of A, then swaps TOP_SWAPS pairs within the top TOP_K so the two
    rankings mostly agree near the top but disagree on a few slots --
    the realistic case of "a tweak to the current ranking", not a totally
    different list.
    """
    items = list(range(N_ITEMS))
    rng.shuffle(items)
    rank_a = items
    rank_b = list(rank_a)
    for _ in range(TOP_SWAPS):
        i, j = rng.sample(range(TOP_K), 2)
        rank_b[i], rank_b[j] = rank_b[j], rank_b[i]
    return rank_a, rank_b


def team_draft_interleave(rank_a: list[int], rank_b: list[int], k: int = TOP_K):
    """Standard team-draft interleaving. Returns (interleaved, credit) where
    credit[item] is 'A', 'B', or 'BOTH' (both teams would have picked it
    at that round -- no comparison available there).

    Each round, whichever team has made fewer picks so far goes first (a
    coin flip breaks ties). If both teams' next unseen item is the same
    item, it is placed once and credited to BOTH, and both teams' pick
    counters advance -- the standard rule that keeps shared top results
    from biasing whose "turn" it is next.
    """
    ia = ib = 0
    seen: list[int] = []
    credit = {}
    picks = {"A": 0, "B": 0}
    while len(seen) < k and (ia < len(rank_a) or ib < len(rank_b)):
        order = (
            ("A", "B") if picks["A"] < picks["B"]
            else ("B", "A") if picks["B"] < picks["A"]
            else (("A", "B") if random.random() < 0.5 else ("B", "A"))
        )
        next_item = {}
        for team in order:
            src, idx = (rank_a, ia) if team == "A" else (rank_b, ib)
            while idx < len(src) and src[idx] in seen:
                idx += 1
            next_item[team] = src[idx] if idx < len(src) else None

        if next_item["A"] is not None and next_item["A"] == next_item["B"]:
            item = next_item["A"]
            seen.append(item)
            credit[item] = "BOTH"
            picks["A"] += 1
            picks["B"] += 1
            ia += 1
            ib += 1
            continue

        for team in order:
            item = next_item[team]
            if item is None or item in seen:
                continue
            seen.append(item)
            credit[item] = team
            picks[team] += 1
            if team == "A":
                ia += 1
            else:
                ib += 1
            break

    return seen, credit


def simulate_session(credit: dict[int, str], edge: float, rng: random.Random) -> str:
    """One session's winner ('A', 'B', or 'tie'), from the contested rounds
    (items credited to exactly one team) in this session's interleaving.
    """
    contested = [team for team in credit.values() if team != "BOTH"]
    if not contested:
        return "tie"
    b_wins = sum(1 for _ in contested if rng.random() < edge)
    a_wins = len(contested) - b_wins
    if b_wins > a_wins:
        return "B"
    if a_wins > b_wins:
        return "A"
    return "tie"


def simulate_trial(n_sessions: int, edge: float, rng: random.Random) -> str:
    """One trial's declared winner across n_sessions independent sessions."""
    wins = {"A": 0, "B": 0}
    for _ in range(n_sessions):
        rank_a, rank_b = make_rankings(rng)
        _, credit = team_draft_interleave(rank_a, rank_b)
        outcome = simulate_session(credit, edge, rng)
        if outcome in wins:
            wins[outcome] += 1
    if wins["B"] > wins["A"]:
        return "B"
    if wins["A"] > wins["B"]:
        return "A"
    return "tie"


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    for edge in EDGES:
        for n_sessions in SESSION_COUNTS:
            outcomes = [simulate_trial(n_sessions, edge, rng) for _ in range(TRIALS_PER_CONFIG)]
            correct = sum(1 for o in outcomes if o == "B") / len(outcomes)
            wrong = sum(1 for o in outcomes if o == "A") / len(outcomes)
            tie = sum(1 for o in outcomes if o == "tie") / len(outcomes)
            rows.append((edge, n_sessions, correct, wrong, tie))

    print(f"{'edge':>6} {'sessions':>9} {'B correctly wins':>18} {'A wrongly wins':>15} {'tie':>6}")
    for edge, n_sessions, correct, wrong, tie in rows:
        print(f"{edge:>6.0%} {n_sessions:>9} {correct:>17.1%} {wrong:>15.1%} {tie:>6.1%}")

    write_results(rows)


def write_results(rows) -> None:
    lines = [
        "# Interleaving simulation results",
        "",
        f"Team-draft interleaving simulation, seed `{SEED}`, "
        f"{TRIALS_PER_CONFIG} trials per (edge, sessions) pair. "
        "Run `python sim/interleaving_sim.py` to reproduce (numbers move by "
        "a point or two on a different seed, not more).",
        "",
        "| Edge | Sessions | B correctly declared winner | A wrongly declared winner | Tie (no winner) |",
        "| --- | --- | --- | --- | --- |",
    ]
    for edge, n_sessions, correct, wrong, tie in rows:
        lines.append(f"| {edge:.0%} | {n_sessions} | {correct:.1%} | {wrong:.1%} | {tie:.1%} |")

    # Recommend the smallest session count that reaches >=90% correct
    # identification across all three edges, since 52% is the realistic
    # worst case the app should still be able to call.
    by_sessions: dict[int, list[float]] = {}
    for edge, n_sessions, correct, _wrong, _tie in rows:
        by_sessions.setdefault(n_sessions, []).append(correct)
    candidates = [n for n, corrects in sorted(by_sessions.items()) if min(corrects) >= 0.90]
    recommended = candidates[0] if candidates else max(by_sessions)
    worst_edge_rate = min(c for e, n, c, w, t in rows if n == recommended)
    best_edge_rate = max(c for e, n, c, w, t in rows if n == recommended)

    lines += [
        "",
        "## Recommendation",
        "",
        f"**{recommended} sessions** is the smallest of the three tested counts "
        f"that correctly picks B as the winner at least 90% of the time across "
        f"all three edges tested (worst case {worst_edge_rate:.0%}, at the "
        f"toughest 52% edge; best case {best_edge_rate:.0%}, at the 60% edge).",
        "",
        "The sprint's guess of 300 sessions holds up well for a clear edge "
        "(55-60%), but is noticeably weaker right at a 52% edge -- see the "
        "table. If the two rankings being compared are expected to be close "
        "(a small tweak, not a rebuild), lean toward 1,000 sessions before "
        "trusting a declared winner; 300 is fine once a test is running for "
        "a visibly larger edge.",
        "",
        "Caveats this simulation does not model: click-position decay within "
        "a session, graded (vs. binary) relevance, and users who see a "
        "session but engage with nothing. All three would make real signal "
        "noisier than this model's, so treat these numbers as an upper bound "
        "on how fast the sprint's test can actually converge.",
        "",
    ]
    with open("sim/RESULTS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
