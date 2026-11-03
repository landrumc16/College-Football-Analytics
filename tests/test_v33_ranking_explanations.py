import pytest
from cfb_analytics.rankings import explain_rank_scores, rank_scores


def test_explanations_reconcile_with_incumbent_scores():
    rows = [("A", 10, -3, 5), ("B", 7, 2, 8), ("C", 8, 1, 6)]
    for weight in (0, 0.3, 0.5, 1):
        explanations = explain_rank_scores(rows, weight)
        scores = rank_scores(rows, weight)
        assert [(item["team"], item["score"]) for item in explanations] == pytest.approx(scores) if False else [item["team"] for item in explanations] == [team for team, _ in scores]
        for item, (_, score) in zip(explanations, scores):
            assert item["score"] == pytest.approx(score)
            assert item["score"] == pytest.approx(item["wins_contribution"] + item["rating_contribution"] + item["tie_break_contribution"])


def test_empty_and_duplicate_teams():
    assert explain_rank_scores([]) == []
    with pytest.raises(ValueError, match="Duplicate team"):
        explain_rank_scores([("A", 1, 2, 3), ("A", 2, 3, 4)])


def test_invalid_weight():
    with pytest.raises(ValueError):
        explain_rank_scores([("A", 1, 2, 3)], 2)
