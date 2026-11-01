import pytest
from cfb_analytics.ingestion import normalize_cfbd_games, snapshot_summary


def test_normalization_and_summary():
    rows = [
        {"id": 101, "season": 2026, "week": 1, "home_team": "A", "away_team": "B",
         "completed": True, "home_points": 21, "away_points": 14, "neutral_site": False},
        {"id": 102, "season": 2026, "week": 2, "home_team": "B", "away_team": "A",
         "completed": False, "home_points": None, "away_points": None, "neutral_site": True},
    ]
    games = normalize_cfbd_games(rows, 2026)
    assert snapshot_summary(games) == {"scheduled": 2, "completed": 1, "pending": 1}
    assert games[1].home_score is None
    assert games[1].neutral_site


def test_duplicate_ids_are_deduplicated():
    row = {"id": 1, "season": 2026, "week": 1, "home_team": "A", "away_team": "B",
           "completed": True, "home_points": 7, "away_points": 3}
    assert len(normalize_cfbd_games([row, row], 2026)) == 1


def test_conflicting_duplicates_are_rejected():
    row = {"id": 1, "season": 2026, "week": 1, "home_team": "A", "away_team": "B",
           "completed": True, "home_points": 7, "away_points": 3}
    with pytest.raises(ValueError):
        normalize_cfbd_games([row, {**row, "home_points": 8}], 2026)


def test_incomplete_scores_rejected():
    with pytest.raises(ValueError):
        normalize_cfbd_games([{"id": 1, "season": 2026, "week": 1,
                              "home_team": "A", "away_team": "B",
                              "completed": True, "home_points": None,
                              "away_points": 3}], 2026)
