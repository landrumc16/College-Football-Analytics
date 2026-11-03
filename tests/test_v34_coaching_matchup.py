from cfb_analytics.v34_coaching_matchup import coaching_matchup_report


def test_coaching_and_scheme_report_preserves_missing_staff():
    game = {"game_id": 1, "home": "Georgia", "away": "Alabama",
            "kickoff": "2025-10-04T20:00:00Z"}
    result = coaching_matchup_report([game], [], [],
             cutoff_by_game={1: "2025-10-04T19:00:00Z"},
             prior_cutoff_by_game={1: "2024-10-04T19:00:00Z"})
    match = result["matchups"][0]
    assert match["home_staff"] is None
    assert match["away_staff"] is None
    assert match["covered_metrics"] == 0
