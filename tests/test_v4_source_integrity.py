import pytest

from cfb_analytics.v4_source_integrity import validate_season_games


def game(**overrides):
    row = dict(season=2024, game_id="1", week=1,
               kickoff="2024-09-01T19:00:00+00:00",
               home="A", away="B", home_score=21, away_score=14,
               home_division="FBS", away_division="FBS",
               fbs_game=True, fbs_participant=True)
    row.update(overrides)
    return row


def test_valid_fbs_and_fcs_coverage():
    rows = [game(), game(game_id="2", away="C", away_division="FCS",
                         fbs_game=False)]
    assert validate_season_games(rows, 2024) == dict(
        season=2024, games=2, fbs_fbs=1, fbs_fcs=1, other_fbs_opponent=0)


@pytest.mark.parametrize("overrides", [
    {"season": 2025}, {"week": None}, {"kickoff": "2024-09-01"},
    {"kickoff": "not a date"}, {"home_score": -1},
    {"home_score": True}, {"away": "A"}, {"fbs_participant": False},
    {"fbs_game": True, "away_division": "FCS"},
    {"fbs_game": False, "home_division": "UNKNOWN", "away_division": "FCS"},
])
def test_invalid_source_rows_rejected(overrides):
    with pytest.raises(ValueError):
        validate_season_games([game(**overrides)], 2024)


def test_duplicate_and_empty_rejected():
    with pytest.raises(ValueError):
        validate_season_games([game(), game()], 2024)
    with pytest.raises(ValueError):
        validate_season_games([], 2024)
