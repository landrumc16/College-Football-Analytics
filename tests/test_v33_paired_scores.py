import pytest

from scripts.v33_paired_scores import paired_score, calibration_bins


def row(game, probability, won=1, season=2025):
    return {"season": season, "game_id": game,
            "home_probability": probability, "home_won": won}


def test_identical_forecasts_have_zero_paired_error():
    rows = [row(1, .8), row(2, .2, 0)]
    score = paired_score(rows, list(reversed(rows)))
    assert score["games"] == 2
    assert score["brier_delta"] == pytest.approx(0)
    assert score["logloss_delta"] == pytest.approx(0)


def test_candidate_improvement_reduces_paired_losses():
    score = paired_score([row(1, .6), row(2, .4, 0)],
                         [row(2, .2, 0), row(1, .8)])
    assert score["brier_delta"] < 0
    assert score["logloss_delta"] < 0
    assert score["brier_delta_standard_error"] is not None


def test_empty_and_singleton():
    assert paired_score([], [])["brier_delta"] is None
    assert paired_score([row(1, .5)], [row(1, .6)])["brier_delta_standard_error"] is None


@pytest.mark.parametrize("base,trial", [
    ([row(1, .5)], []),
    ([row(1, .5)], [row(2, .5)]),
    ([row(1, .5)], [row(1, .5, 0)]),
])
def test_rejects_misaligned_or_conflicting_games(base, trial):
    with pytest.raises(ValueError):
        paired_score(base, trial)


def test_rejects_duplicate_and_invalid_probabilities():
    with pytest.raises(ValueError, match="Duplicate"):
        paired_score([row(1, .5), row(1, .5)], [])
    with pytest.raises(ValueError, match="Invalid"):
        paired_score([row(1, 1.1)], [row(1, .5)])


def test_calibration_bins_partition_and_edge_probabilities():
    bins = calibration_bins([row(1, 0, 0), row(2, 1, 1), row(3, .55, 1)], bins=2)
    assert [b["games"] for b in bins] == [1, 2]
    assert bins[0]["observed_rate"] == 0
    assert bins[1]["observed_rate"] == 1
    assert bins[1]["mean_probability"] == pytest.approx(.775)


def test_calibration_empty_bins_and_validation():
    assert all(b["observed_rate"] is None for b in calibration_bins([], bins=3))
    with pytest.raises(ValueError):
        calibration_bins([], bins=1)
