import pytest
from cfb_analytics.rankings import rank_scores


def test_order_by_projected_wins():
    rows = [('A', 10, -5, 4), ('B', 5, 5, 5)]
    assert rank_scores(rows, 1)[0][0] == 'A'


def test_order_by_rating():
    rows = [('A', 10, -5, 4), ('B', 5, 5, 5)]
    assert rank_scores(rows, 0)[0][0] == 'B'


def test_tie_break_by_sheet_row():
    rows = [('A', 8, 2, 4), ('B', 8, 2, 5)]
    assert rank_scores(rows)[0][0] == 'A'


def test_invalid_weight():
    with pytest.raises(ValueError):
        rank_scores([('A', 8, 2, 4)], -0.1)
