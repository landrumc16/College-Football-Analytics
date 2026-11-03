"""Additional safeguards for research-only paired scoring."""
import pytest
from scripts.v33_paired_scores import paired_score, calibration_bins


def row(season, game, probability, outcome):
    return {"season": season, "game_id": game,
            "home_probability": probability, "home_won": outcome}


@pytest.mark.parametrize("probability", [float("nan"), float("inf"), -0.01, 1.01, True])
def test_invalid_probability_rejected(probability):
    with pytest.raises(ValueError):
        calibration_bins([row(2025, "a", probability, 1)])


def test_mismatched_outcomes_rejected():
    with pytest.raises(ValueError, match="Conflicting outcomes"):
        paired_score([row(2025, "a", 0.7, 1)], [row(2025, "a", 0.7, 0)])


def test_same_game_alignment_is_order_independent():
    a = [row(2024, "a", 0.8, 1), row(2025, "b", 0.3, 0)]
    b = [row(2025, "b", 0.2, 0), row(2024, "a", 0.7, 1)]
    assert paired_score(a, b) == paired_score(list(reversed(a)), list(reversed(b)))
