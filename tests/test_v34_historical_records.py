import pytest
from cfb_analytics.v34_historical_records import historical_season_records


def raw_game(id, season, home, away, hs, ass):
    return {"id": id, "season": season, "week": 1,
            "home_team": home, "away_team": away,
            "home_points": hs, "away_points": ass,
            "completed": True, "neutral_site": False}


def test_historical_records_include_fcs_wins():
    rows = historical_season_records({2024: [raw_game(1, 2024, "Georgia", "FCS", 40, 7),
                                              raw_game(2, 2024, "Alabama", "Georgia", 10, 14)]},
                                     fbs_teams_by_season={2024: {"Georgia", "Alabama"}},
                                     completed_seasons={2024})
    ga = next(x for x in rows if x["team"] == "Georgia")
    assert ga["actual_wins"] == 2
    assert ga["fcs_or_other_opponent_games"] == 1


def test_missing_fbs_classification_fails_closed():
    with pytest.raises(ValueError, match="classification"):
        historical_season_records({2024: [raw_game(1, 2024, "Georgia", "FCS", 40, 7)]},
                                  fbs_teams_by_season={}, completed_seasons={2024})
