import pytest
from cfb_analytics.pipeline import build_season_report


ROSTER = [
    {"name": "A", "conference": "ACC", "prior": 10},
    {"name": "B", "conference": "ACC", "prior": -10},
    {"name": "C", "conference": "Independent", "prior": 0},
] + [
    {"name": f"Fixture {i}", "conference": f"Fixture League {i // 2}", "prior": -20}
    for i in range(9)
]


def game(game_id, home, away, *, completed=False, hs=None, ass=None, neutral=False):
    return {"game_id": game_id, "season": 2026, "week": game_id,
            "home": home, "away": away, "completed": completed,
            "home_score": hs, "away_score": ass, "neutral_site": neutral,
            "start_date": "2026-11-01T18:00:00Z"}


def test_complete_season_pipeline():
    snapshot = {"season": 2026, "source": "test", "games": [
        game(1, "A", "B", completed=True, hs=28, ass=14),
        game(2, "B", "A"),
        game(3, "C", "FCS", neutral=True),
    ]}
    report = build_season_report(snapshot, ROSTER)
    assert report["summary"] == {"teams": 12, "completed_games": 1, "upcoming_games": 2}
    assert len(report["rankings"]) == 12
    assert {r["rank"] for r in report["rankings"]} == set(range(1, 13))
    a = next(r for r in report["rankings"] if r["team"] == "A")
    assert a["wins"] == 1
    assert a["projected_conference_wins"] > 1
    assert len(report["projected_bracket"]["seeds"]) == 12
    assert len(report["projected_bracket"]["first_round"]) == 4
    assert sum(seed["bid"] == "automatic" for seed in report["projected_bracket"]["seeds"]) == 5
    assert len(report["predictions"]) == 2
    assert all(0 <= p["home_win_probability"] <= 1 for p in report["predictions"])


def test_reject_mixed_seasons():
    with pytest.raises(ValueError):
        build_season_report({"season": 2026, "games": [
            {**game(1, "A", "B"), "season": 2025}
        ]}, ROSTER)


def test_reject_duplicate_game_ids():
    g = game(1, "A", "B")
    with pytest.raises(ValueError):
        build_season_report({"season": 2026, "games": [g, g]}, ROSTER)


def test_reject_completed_game_with_missing_score():
    with pytest.raises(ValueError, match="missing score"):
        build_season_report({"season": 2026, "games": [
            game(1, "A", "B", completed=True, hs=None, ass=7)
        ]}, ROSTER)


def test_report_preserves_data_provenance():
    report = build_season_report({"season": 2026, "source": "test-source",
                                  "retrieved_at": "2026-10-31T00:00:00+00:00",
                                  "data_changed_at": "2026-10-30T00:00:00+00:00",
                                  "games": []}, ROSTER)
    assert report["source"] == "test-source"
    assert report["retrieved_at"] == "2026-10-31T00:00:00+00:00"
    assert report["data_changed_at"] == "2026-10-30T00:00:00+00:00"


def test_reject_empty_roster():
    with pytest.raises(ValueError, match="Roster"):
        build_season_report({"season": 2026, "games": []}, [])


def test_reject_self_matchup():
    with pytest.raises(ValueError, match="self-matchup"):
        build_season_report({"season": 2026, "games": [game(1, "A", "A")]}, ROSTER)


def test_miami_cfbd_alias_counts_wins_for_miami_florida():
    roster = ROSTER + [{"name": "Miami (FL)", "conference": "ACC", "prior": 15},
                       {"name": "Miami (OH)", "conference": "MAC", "prior": 0}]
    snapshot = {"season": 2026, "games": [
        game(1, "Miami", "A", completed=True, hs=31, ass=14),
        game(2, "Miami (OH)", "B", completed=True, hs=21, ass=10),
        game(3, "B", "Miami"),
    ]}
    report = build_season_report(snapshot, roster)
    rankings = {r["team"]: r for r in report["rankings"]}
    assert rankings["Miami (FL)"]["wins"] == 1
    assert rankings["Miami (FL)"]["projected_wins"] > 1
    assert rankings["Miami (OH)"]["wins"] == 1
    assert any(p["away"] == "Miami (FL)" for p in report["predictions"])


def test_all_verified_cfbd_fbs_aliases_are_reconciled():
    aliases = [("Miami", "Miami (FL)"),
               ("App State", "Appalachian State"),
               ("Sam Houston", "Sam Houston State"),
               ("UL Monroe", "ULM")]
    roster = ROSTER + [{"name": canonical, "conference": "ACC", "prior": 10}
                       for _, canonical in aliases]
    snapshot = {"season": 2026, "games": [
        game(i + 1, feed, "A", completed=True, hs=28, ass=7)
        for i, (feed, _) in enumerate(aliases)
    ]}
    report = build_season_report(snapshot, roster)
    by_team = {row["team"]: row for row in report["rankings"]}
    for _, canonical in aliases:
        assert by_team[canonical]["wins"] == 1


def test_live_cfbd_report_rejects_roster_team_missing_from_feed():
    snapshot = {"season": 2026, "source": "collegefootballdata.com/games",
                "games": [game(1, "A", "B", completed=True, hs=20, ass=10)]}
    with pytest.raises(ValueError, match="FBS roster schools absent"):
        build_season_report(snapshot, ROSTER)


def test_schedule_includes_completed_and_future_games_with_canonical_names():
    roster = ROSTER + [{"name": "Miami (FL)", "conference": "ACC", "prior": 15}]
    snapshot = {"season": 2026, "games": [
        game(1, "Miami", "A", completed=True, hs=31, ass=14),
        game(2, "B", "Miami"),
    ]}
    report = build_season_report(snapshot, roster)
    schedule = report["schedule"]
    assert len(schedule) == 2
    assert schedule[0]["home"] == "Miami (FL)"
    assert schedule[0]["completed"] is True
    assert schedule[0]["home_score"] == 31
    assert schedule[1]["away"] == "Miami (FL)"
    assert schedule[1]["completed"] is False
    assert schedule[1]["home_score"] is None
    assert any(p["game_id"] == schedule[1]["game_id"] for p in report["predictions"])


def test_performance_uses_archived_forecasts_only():
    from cfb_analytics.pipeline import build_performance_against_expectations
    snapshot = {"games": [game(1, "Miami", "A", completed=True, hs=24, ass=14),
                          game(2, "A", "B", completed=True, hs=10, ass=17)]}
    roster = ROSTER + [{"name": "Miami (FL)", "conference": "ACC", "prior": 10}]
    history = {"1": {"home": "Miami (FL)", "away": "A", "home_win_probability": 0.3, "forecast_recorded_at": "2026-11-01T17:00:00Z"}}
    rows = build_performance_against_expectations(snapshot, roster, history)
    assert rows["Miami (FL)"]["actual_wins"] == 1
    assert rows["Miami (FL)"]["expected_wins"] == 0.3
    assert rows["Miami (FL)"]["wins_above_expected"] == 0.7
    assert rows["A"]["expected_wins"] == 0.7
    assert rows["B"]["games_with_forecasts"] == 0
    assert rows["B"]["wins_above_expected"] is None


def test_performance_rejects_wrong_matchup_and_invalid_probability():
    from cfb_analytics.pipeline import build_performance_against_expectations
    snapshot = {"games": [game(1, "A", "B", completed=True, hs=21, ass=14)]}
    for bad in ({"home": "B", "away": "A", "home_win_probability": 0.8, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
                {"home": "A", "away": "B", "home_win_probability": 1.2, "forecast_recorded_at": "2026-11-01T17:00:00Z"}):
        rows = build_performance_against_expectations(snapshot, ROSTER, {"1": bad})
        assert rows["A"]["games_with_forecasts"] == 0
        assert rows["A"]["wins_above_expected"] is None


def test_prediction_accuracy_only_uses_archived_completed_forecasts():
    from cfb_analytics.pipeline import build_prediction_accuracy
    snapshot = {"games": [
        game(1, "A", "B", completed=True, hs=21, ass=14),
        game(2, "B", "A", completed=True, hs=7, ass=17),
        game(3, "A", "B", completed=True, hs=28, ass=7),
        game(4, "A", "B", completed=False),
    ]}
    history = {
        "1": {"home": "A", "away": "B", "home_win_probability": 0.8, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
        "2": {"home": "B", "away": "A", "home_win_probability": 0.7, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
        "3": {"home": "B", "away": "A", "home_win_probability": 0.9, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
        "4": {"home": "A", "away": "B", "home_win_probability": 0.9, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
    }
    result = build_prediction_accuracy(snapshot, history)
    assert {key: result[key] for key in ("games_evaluated", "correct_winners", "winner_accuracy", "brier_score")} == {"games_evaluated": 2, "correct_winners": 1,
                      "winner_accuracy": 0.5, "brier_score": 0.265}
    assert result["log_loss"] is not None
    assert result["margin_mae"] is None
    assert sum(row["games"] for row in result["calibration"]) == 2


def test_prediction_accuracy_empty_history_has_no_misleading_percentage():
    from cfb_analytics.pipeline import build_prediction_accuracy
    result = build_prediction_accuracy({"games": [game(1, "A", "B", completed=True, hs=21, ass=14)]}, {})
    assert result["games_evaluated"] == 0
    assert result["winner_accuracy"] is None
    assert result["brier_score"] is None


def test_prediction_accuracy_rejects_boolean_probability():
    from cfb_analytics.pipeline import build_prediction_accuracy
    snapshot = {"games": [game(1, "A", "B", completed=True, hs=21, ass=14)]}
    history = {"1": {"home": "A", "away": "B", "home_win_probability": True, "forecast_recorded_at": "2026-11-01T17:00:00Z"}}
    result = build_prediction_accuracy(snapshot, history)
    assert result["games_evaluated"] == 0
    assert result["winner_accuracy"] is None


def test_prediction_accuracy_reconciles_miami_alias():
    from cfb_analytics.pipeline import build_prediction_accuracy
    snapshot = {"games": [game(1, "Miami", "A", completed=True, hs=31, ass=10)]}
    history = {"1": {"home": "Miami (FL)", "away": "A", "home_win_probability": 0.75, "forecast_recorded_at": "2026-11-01T17:00:00Z"}}
    result = build_prediction_accuracy(snapshot, history)
    assert result["games_evaluated"] == 1
    assert result["correct_winners"] == 1
    assert result["brier_score"] == 0.0625


def test_prediction_accuracy_fbs_only_excludes_unmodeled_matchups():
    from cfb_analytics.pipeline import build_prediction_accuracy
    snapshot = {"games": [
        game(101, "A", "B", completed=True, hs=28, ass=14),
        game(102, "A", "Unmodeled College", completed=True, hs=7, ass=21),
        game(103, "Unmodeled College", "B", completed=True, hs=21, ass=7),
    ]}
    history = {
        "101": {"home": "A", "away": "B", "home_win_probability": 0.75, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
        "102": {"home": "A", "away": "Unmodeled College", "home_win_probability": 0.75, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
        "103": {"home": "Unmodeled College", "away": "B", "home_win_probability": 0.75, "forecast_recorded_at": "2026-11-01T17:00:00Z"},
    }
    result = build_prediction_accuracy(snapshot, history, eligible_teams={"A", "B"})
    assert {key: result[key] for key in ("games_evaluated", "correct_winners", "winner_accuracy", "brier_score")} == {"games_evaluated": 1, "correct_winners": 1,
                      "winner_accuracy": 1.0, "brier_score": 0.0625}
    assert result["evaluation_scope"] == "archived_pregame_fbs_vs_fbs"


def test_prediction_accuracy_fbs_only_empty_sample_is_not_zero_percent():
    from cfb_analytics.pipeline import build_prediction_accuracy
    snapshot = {"games": [game(104, "A", "Unmodeled College", completed=True, hs=21, ass=14)]}
    history = {"104": {"home": "A", "away": "Unmodeled College", "home_win_probability": 0.7, "forecast_recorded_at": "2026-11-01T17:00:00Z"}}
    result = build_prediction_accuracy(snapshot, history, eligible_teams={"A", "B"})
    assert result["games_evaluated"] == 0
    assert result["winner_accuracy"] is None
    assert result["brier_score"] is None


def test_fcs_results_and_future_games_flow_through_full_report():
    """Workbook parity: FCS scores affect FBS records and future FCS forecasts remain."""
    snapshot = {"season": 2026, "source": "test", "games": [
        game(1, "A", "FCS Visitor", completed=True, hs=55, ass=7),
        game(2, "FCS Host", "B", completed=True, hs=21, ass=24),
        game(3, "C", "FCS Future"),
    ]}
    report = build_season_report(snapshot, ROSTER)
    ranked = {row["team"]: row for row in report["rankings"]}
    assert ranked["A"]["wins"] == 1
    assert ranked["B"]["wins"] == 1
    assert report["summary"]["completed_games"] == 2
    assert report["summary"]["upcoming_games"] == 1
    assert report["predictions"][0]["away"] == "FCS Future"
    assert any(row["away"] == "FCS Visitor" and row["home_score"] == 55
               for row in report["schedule"])
    assert any(row["home"] == "FCS Host" and row["away_score"] == 24
               for row in report["schedule"])
    assert all(row["team"] not in {"FCS Visitor", "FCS Host", "FCS Future"}
               for row in report["rankings"])
    assert ranked["C"]["projected_wins"] > ranked["C"]["wins"]
