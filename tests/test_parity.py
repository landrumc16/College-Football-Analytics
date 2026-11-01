"""Structural checks for the frozen spreadsheet parity baseline.

These tests do not assert numerical parity; that is checked separately by
python -m cfb_analytics.parity --strict.
"""
from collections import Counter

from cfb_analytics.parity import compare, load_baseline


def test_frozen_spreadsheet_fixture_is_complete_and_unique():
    teams, games = load_baseline()
    assert len(teams) == 138
    assert len(games) == 510
    names = [team["name"] for team in teams]
    assert len(names) == len(set(names))
    assert all(team["conference"] and isinstance(team["prior"], (int, float))
               for team in teams)
    assert all(len(team["passes"]) == 8 for team in teams)
    assert all(game["home"] != game["away"] for game in games)
    assert all(isinstance(game["home_score"], int)
               and isinstance(game["away_score"], int) for game in games)
    participants = Counter(name for game in games
                           for name in (game["home"], game["away"]))
    assert all(participants[name] > 0 for name in names)


def test_spreadsheet_parity_comparison_produces_finite_deltas():
    """Fail CI for missing/broken baseline, not for known model discrepancies."""
    differences = compare()
    assert differences
    assert all(0 <= delta < float("inf") for delta, *_ in differences)
    assert all(team and field for _, team, field, _, _ in differences)
