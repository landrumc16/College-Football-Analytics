from cfb_analytics.v34_combined_matchup import combined_matchup_report


def test_combined_matchup_handles_sparse_observations():
    game = {"game_id": 1, "home": "Georgia", "away": "Alabama",
            "kickoff": "2025-10-04T20:00:00Z"}
    result = combined_matchup_report([game], [], [], [],
               cutoff_by_game={1: "2025-10-04T19:00:00Z"},
               prior_cutoff_by_game={1: "2024-10-04T19:00:00Z"})
    match = result["matchups"][0]
    assert match["talent_features_covered"] == 0
    assert match["scheme_metrics_covered"] == 0
    assert match["home_staff"] is None
    assert match["away_staff"] is None
