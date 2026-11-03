from cfb_analytics.v34_recruiting_evaluation_cli import evaluate_snapshot


def test_snapshot_entrypoint_evaluates_complete_seasons():
    classes = []
    games = {}
    members = {}
    for year in range(2019, 2024):
        classes.append({"season": year, "team": "Georgia", "recruiting_points": 200,
                        "source": "CFBD", "retrieved_at": "2026-11-03T00:00:00Z"})
        games[str(year)] = [{"id": year, "season": year, "week": 1,
                             "home_team": "Georgia", "away_team": "FCS Team",
                             "home_points": 14, "away_points": 7, "completed": True}]
        members[str(year)] = ["Georgia"]
    result = evaluate_snapshot({"classes": classes, "games_by_season": games,
                "fbs_teams_by_season": members, "completed_seasons": list(range(2019, 2024))})
    assert result["joined_team_seasons"] == 5
    assert result["scorecard"]["heldout_seasons"] == 2
    assert result["historical_asof_verified"] is False
