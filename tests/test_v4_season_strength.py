from cfb_analytics.v4_season_strength import retrospective_season_ratings


def game(game_id, home, away, hs, aws, kickoff="2025-09-01T17:00:00+00:00", neutral=False):
    return {"season": 2025, "game_id": game_id, "week": 1, "kickoff": kickoff,
            "home": home, "away": away, "home_score": hs, "away_score": aws,
            "home_division": "FBS", "away_division": "FBS",
            "fbs_game": True, "fbs_participant": True, "neutral_site": neutral}


def test_opponent_results_affect_subsequent_strength():
    schedule = [game("1", "A", "B", 24, 10),
                game("2", "A", "C", 24, 10, "2025-09-08T17:00:00+00:00")]
    result = retrospective_season_ratings(schedule, 2025)
    ratings = {r["team"]: r["rating"] for r in result["teams"]}
    assert ratings["A"] > ratings["C"]
    assert ratings["B"] < 1500
    assert result["predictive_validation"] is False
    assert result["comparable_across_seasons_verified"] is False


def test_order_independent_for_simultaneous_games():
    rows = [game("1", "A", "B", 20, 10),
            game("2", "A", "C", 20, 10)]
    a = retrospective_season_ratings(rows, 2025)
    b = retrospective_season_ratings(list(reversed(rows)), 2025)
    assert a == b


def test_neutral_field_changes_expectation():
    home = retrospective_season_ratings([game("1", "A", "B", 21, 7)], 2025)
    neutral = retrospective_season_ratings([game("1", "A", "B", 21, 7, neutral=True)], 2025)
    assert neutral["teams"][0]["rating"] > home["teams"][0]["rating"]
