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
