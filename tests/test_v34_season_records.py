import pytest
from cfb_analytics.ingestion import IngestedGame
from cfb_analytics.v34_season_records import season_records


def game(id, home, away, hs, ass, completed=True):
    return IngestedGame(game_id=id, season=2025, week=1, home=home, away=away,
                        completed=completed, home_score=hs, away_score=ass,
                        neutral_site=False)


def test_fcs_games_count_for_records_but_not_as_fbs_team():
    rows = season_records([game(1, "Georgia", "FCS Opponent", 42, 7),
                           game(2, "Alabama", "Georgia", 21, 24),
                           game(3, "Georgia", "TBD", None, None, False)],
                          eligible_teams={"Georgia", "Alabama"})
    ga = next(row for row in rows if row["team"] == "Georgia")
    assert (ga["actual_wins"], ga["games_played"], ga["fcs_or_other_opponent_games"]) == (2, 2, 1)
    assert all(row["team"] != "FCS Opponent" for row in rows)


def test_duplicate_game_ids_rejected():
    row = game(1, "Georgia", "Alabama", 21, 14)
    with pytest.raises(ValueError, match="Duplicate"):
        season_records([row, row], eligible_teams={"Georgia", "Alabama"})
