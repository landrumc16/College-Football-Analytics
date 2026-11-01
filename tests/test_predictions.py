import pytest
from cfb_analytics.predictions import predict


def test_model_and_market_are_distinct():
    p = predict('Delaware', 'Missouri State', -9.006025282, -10.86048646, closing_home_spread=-3)
    assert p.home_margin == pytest.approx(4.854461178)
    assert p.model_home_probability == pytest.approx(0.6504435481, abs=1e-6)
    assert p.published_home_probability == pytest.approx(0.588, abs=0.001)
    assert p.winner == 'Delaware'
    assert p.confidence == 'Lean'


def test_neutral_site_skips_home_advantage():
    p = predict('A', 'B', 10, 10, neutral=True)
    assert p.home_margin == 0
    assert p.published_home_probability == 0.5
