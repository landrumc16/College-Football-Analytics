from cfb_analytics.v34_recruiting_evaluation import evaluate_historical_recruiting


def test_end_to_end_recruiting_holdout_includes_fcs():
    classes, games, members = [], {}, {}
    for season in range(2019, 2024):
        classes.append({"season": season, "team": "Georgia", "recruiting_points": 300,
                        "source": "CFBD", "retrieved_at": "2026-11-03T00:00:00Z"})
        games[season] = [{"id": season, "season": season, "week": 1,
                          "home_team": "Georgia", "away_team": "FCS Team",
                          "home_points": 28, "away_points": 7, "completed": True}]
        members[season] = {"Georgia"}
    result = evaluate_historical_recruiting(classes, games,
                fbs_teams_by_season=members, completed_seasons=set(games))
    assert result["joined_team_seasons"] == 5
    assert result["scorecard"]["heldout_seasons"] == 2
    assert result["scorecard"]["win_mae"] == 0
    assert result["historical_asof_verified"] is False


def test_incomplete_season_excluded():
    result = evaluate_historical_recruiting([{"season": 2026, "team": "Georgia"}], {},
                  fbs_teams_by_season={}, completed_seasons=set())
    assert result["excluded"]["incomplete_season"] == 1
    assert result["scorecard"]["evaluated_team_seasons"] == 0
