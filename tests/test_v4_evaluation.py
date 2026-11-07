import pytest
from cfb_analytics.v4_evaluation import evaluate_pairs


def row(**kwargs):
    result = dict(game_id="g1", season=2024, week=1, outcome=1,
                  incumbent_probability=.6, challenger_probability=.8,
                  prediction_kind="retrospective")
    result.update(kwargs)
    return result


def test_paired_metrics_and_season_partition():
    report = evaluate_pairs([row(), row(game_id="g2", season=2025, outcome=0,
                                         incumbent_probability=.6, challenger_probability=.2)])
    assert report["games"] == 2
    assert report["retrospective"]["relative_brier_reduction"] > 0
    assert set(report["retrospective_by_season"]) == {"2024", "2025"}
    assert not report["promotion_eligible"]


def test_missing_and_prospective_are_not_fabricated():
    assert evaluate_pairs([])["status"] == "insufficient_data"
    with pytest.raises(ValueError, match="archive provenance"):
        evaluate_pairs([row(prediction_kind="prospective")])
    report = evaluate_pairs([row(prediction_kind="prospective", predicted_at="2024-09-01T00:00:00Z",
                                data_as_of="snapshot-1")])
    assert report["retrospective"] is None
    assert report["prospective"]["games"] == 1


def test_reject_duplicate_and_invalid_inputs():
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_pairs([row(), row()])
    with pytest.raises(ValueError, match="Invalid probability"):
        evaluate_pairs([row(challenger_probability=float("nan"))])
    with pytest.raises(ValueError, match="Week"):
        evaluate_pairs([row(week=0)])


def test_clustered_interval_is_reproducible_and_paired():
    from cfb_analytics.v4_evaluation import clustered_brier_interval
    rows = [row(game_id=f"g{i}", week=i, incumbent_probability=.55,
                challenger_probability=.85, outcome=1) for i in range(1, 9)]
    first = clustered_brier_interval(rows, draws=200, seed=7)
    assert first == clustered_brier_interval(rows, draws=200, seed=7)
    assert first["supports_improvement"]
    assert first["ci95_upper"] < 0
    assert first["clusters"] == 8


def test_clustered_interval_rejects_insufficient_and_prospective_cohorts():
    from cfb_analytics.v4_evaluation import clustered_brier_interval
    with pytest.raises(ValueError, match="two independent"):
        clustered_brier_interval([row()], draws=100)
    with pytest.raises(ValueError, match="retrospective"):
        clustered_brier_interval([
            row(game_id="a", prediction_kind="prospective"),
            row(game_id="b", week=2),
        ], draws=100)


def test_release_gate_rejects_incomplete_season_coverage():
    from cfb_analytics.v4_evaluation import assess_release_gates
    with pytest.raises(ValueError, match="Exactly four"):
        assess_release_gates([row()], held_out_seasons=[2024])
    with pytest.raises(ValueError, match="All and only"):
        assess_release_gates([row()], held_out_seasons=[2022, 2023, 2024, 2025])


def test_release_gate_requires_all_numerical_conditions_and_never_promotes():
    from cfb_analytics.v4_evaluation import assess_release_gates
    rows = [row(game_id=f"{season}-{week}", season=season, week=week,
                incumbent_probability=.55, challenger_probability=.85, outcome=1)
            for season in range(2022, 2026) for week in range(1, 5)]
    result = assess_release_gates(rows, held_out_seasons=[2022, 2023, 2024, 2025],
                                  draws=200, seed=7)
    assert result["numerical_gates_pass"]
    assert result["folds_improved"] == 4
    assert result["promotion_eligible"] is False
    assert all(result["criteria"].values())
    weaker = [dict(x, challenger_probability=.2) for x in rows]
    failed = assess_release_gates(weaker, held_out_seasons=[2022, 2023, 2024, 2025],
                                  draws=200, seed=7)
    assert not failed["numerical_gates_pass"]
    assert not failed["criteria"]["brier_reduction_at_least_5_percent"]


def test_clustered_interval_rejects_duplicate_games():
    from cfb_analytics.v4_evaluation import clustered_brier_interval
    with pytest.raises(ValueError, match="Duplicate"):
        clustered_brier_interval([row(), row()], draws=100)


def test_calibration_bins_preserve_coverage_and_probability_endpoints():
    report = evaluate_pairs([
        row(game_id="zero", outcome=0, incumbent_probability=0, challenger_probability=0),
        row(game_id="one", outcome=1, incumbent_probability=1, challenger_probability=1),
    ])["retrospective"]
    for model in ("incumbent", "challenger"):
        bins = report["calibration"][model]
        assert len(bins) == 10
        assert sum(b["games"] for b in bins) == 2
        assert bins[0]["observed_win_rate"] == 0
        assert bins[9]["observed_win_rate"] == 1
        assert bins[1]["mean_probability"] is None
