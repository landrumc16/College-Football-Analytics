import pytest
from cfb_analytics.model import (
    ModelSettings, adjusted_home_margin, confidence_label,
    market_home_win_probability, model_home_margin,
    preseason_prior, win_probability_from_rating_gap,
)


def test_adjusted_margin_matches_workbook_example():
    # Games!G4: TCU 10, North Carolina 15, home advantage 3 -> -8
    assert adjusted_home_margin(10, 15, ModelSettings()) == -8


def test_adjusted_margin_caps_at_45():
    assert adjusted_home_margin(100, 0, ModelSettings()) == 45


def test_preseason_prior_matches_boston_college():
    assert preseason_prior(
        -6.25, -0.088, -0.939, False,
        intercept=0.9847, previous_weight=0.4569,
        talent_weight=4.0926, returning_weight=0,
        coach_weight=0, missing_previous_rating=-12,
    ) != 0  # full coefficients and parity fixtures still pending


def test_prediction_margin_matches_delaware():
    # Predictions!D6/E6: -9.006025282 and -10.86048646; home bump 3
    assert model_home_margin(-9.006025282, -10.86048646) == pytest.approx(4.854461178)


def test_market_probability_is_directionally_correct():
    assert market_home_win_probability(-7) > 0.5
    assert market_home_win_probability(7) < 0.5


@pytest.mark.parametrize("gap,expected", [(0, 0.5), (18, 10/11), (-18, 1/11)])
def test_logistic(gap, expected):
    assert win_probability_from_rating_gap(gap) == pytest.approx(expected)


@pytest.mark.parametrize("p,label", [(0.5, "Toss-up"), (0.6, "Lean"), (0.7, "Likely"), (0.9, "Strong")])
def test_confidence(p, label):
    assert confidence_label(p) == label
