"""Spreadsheet Predictions!F/N/H/O/G parity and market separation."""
from math import isclose

import pytest

from cfb_analytics.workbook_prediction import workbook_prediction


def test_no_market_uses_independent_model():
    result = workbook_prediction("Home", "Away", 10, 0)
    assert result.projected_home_margin == 13
    assert result.displayed_source == "Model"
    assert result.displayed_home_probability == result.model_home_probability
    assert result.displayed_winner == "Home"


def test_market_line_replaces_display_but_not_independent_model():
    without = workbook_prediction("Home", "Away", 10, 0)
    with_line = workbook_prediction(
        "Home", "Away", 10, 0, closing_home_spread=12.5)
    assert with_line.displayed_source == "Market line"
    assert with_line.model_home_probability == without.model_home_probability
    assert with_line.displayed_home_probability < 0.5
    assert with_line.displayed_winner == "Away"
    assert isclose(with_line.displayed_home_probability,
                   1 / (1 + 10 ** (12.5 / 19.5)))


def test_neutral_site_removes_home_edge():
    result = workbook_prediction("Home", "Away", 10, 0, neutral=True)
    assert result.projected_home_margin == 10


def test_even_market_line_is_still_market_assisted():
    result = workbook_prediction(
        "Home", "Away", 0, 0, closing_home_spread=0)
    assert result.displayed_source == "Market line"
    assert result.displayed_home_probability == 0.5
    assert result.displayed_winner == "Home"


@pytest.mark.parametrize("line", [float("nan"), float("inf"), -float("inf")])
def test_invalid_market_lines_rejected(line):
    with pytest.raises(ValueError):
        workbook_prediction("Home", "Away", 0, 0, closing_home_spread=line)
