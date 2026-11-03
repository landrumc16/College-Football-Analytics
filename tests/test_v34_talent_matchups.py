from cfb_analytics.v34_talent_matchups import talent_matchup_report


def test_talent_matchup_uses_only_pregame_publications():
    game = {"game_id": 5, "home": "Georgia", "away": "Alabama",
            "kickoff": "2025-10-04T20:00:00Z"}
    def obs(team, value, stamp):
        return {"team": team, "feature": "returning_production", "value": value,
                "source": "team statistics", "observed_at": stamp, "published_at": stamp}
    rows = [obs("Georgia", .7, "2025-09-01T00:00:00Z"),
            obs("Alabama", .5, "2025-09-01T00:00:00Z"),
            obs("Georgia", .9, "2025-10-05T00:00:00Z")]
    result = talent_matchup_report([game], rows,
                      cutoff_by_game={5: "2025-10-04T19:00:00Z"})
    match = result["matchups"][0]
    assert match["covered_features"] == 1
    assert round(match["comparisons"][0]["home_minus_away"], 4) == .2
