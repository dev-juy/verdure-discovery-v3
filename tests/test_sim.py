import random
from sim.interleaving_sim import simulate_trial, team_draft_interleave


def test_draft_is_balanced_unique_and_reproducible():
    a, b = [1, 1, 2, 3, 4], [3, 5, 6, 7, 8]
    result = team_draft_interleave(a, b, 6, random.Random(8))
    assert result == team_draft_interleave(a, b, 6, random.Random(8))
    feed, credit = result
    assert len(feed) == len(set(feed)) == 6
    assert abs(list(credit.values()).count('A') - list(credit.values()).count('B')) <= 1
    assert all(x in (a if credit[x] == 'A' else b) for x in feed)
    # Once one team exhausts its unique items, the other team fills the feed.
    full, ownership = team_draft_interleave(a, b, 8, random.Random(8))
    assert len(full) == len(set(full)) == 8
    assert all(x in (a if ownership[x] == 'A' else b) for x in full)


def test_no_engagement_and_preference_extremes():
    assert simulate_trial(100, .6, random.Random(0), 0) == 'tie'
    assert simulate_trial(100, 1, random.Random(0)) == 'B'
    assert simulate_trial(100, 0, random.Random(0)) == 'A'
