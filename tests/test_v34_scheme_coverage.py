from cfb_analytics.v34_scheme_coverage import scheme_coverage_report


def test_scheme_coverage_tracks_missing_and_available_metrics():
    games = [{"game_id": 1, "home": "Georgia", "away": "Alabama",
              "kickoff": "2025-10-04T20:00:00Z"},
             {"game_id": 2, "home": "Georgia", "away": "Clemson",
              "kickoff": "2025-10-04T20:00:00Z"}]
    rows = [{"team": team, "feature": "pass_rate", "value": value,
             "source": "official stats", "observed_at": "2025-10-01T00:00:00Z",
             "published_at": "2025-10-02T00:00:00Z"}
            for team, value in (("Georgia", .6), ("Alabama", .4))]
    result = scheme_coverage_report(games, rows,
              cutoff_by_game={1: "2025-10-04T18:00:00Z",
                              2: "2025-10-04T18:00:00Z"})
    assert result["games_evaluated"] == 2
    assert result["games_with_any_scheme_comparison"] == 1
    assert result["coverage_fraction"] == .5
    assert result["metric_game_counts"] == {"pass_rate": 1}
