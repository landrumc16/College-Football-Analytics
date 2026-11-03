import pytest
from cfb_analytics.v34_workbook_prior import (
    workbook_preseason_prior, DEFAULT_LAST_RATING,
)


def test_original_workbook_prior_formula_and_coaching_effect():
    # PreseasonPrior!B9:E9 in original workbook (Miami FL).
    prior = workbook_preseason_prior(last_rating=22.27, talent_z=1.575,
                                     returning_z=-0.176, new_head_coach=False)
    expected = 0.9847 + 0.4569 * 22.27 + 4.0926 * 1.575 + 1.5987 * -0.176
    assert prior == pytest.approx(expected)
    changed = workbook_preseason_prior(last_rating=22.27, talent_z=1.575,
                                       returning_z=-0.176, new_head_coach=True)
    assert changed - prior == pytest.approx(-2.9411)


def test_missing_features_are_not_silently_zeroed():
    for bad in (None, float("nan"), float("inf"), True):
        with pytest.raises(ValueError):
            workbook_preseason_prior(last_rating=DEFAULT_LAST_RATING,
                                     talent_z=bad, returning_z=0.2,
                                     new_head_coach=False)
    with pytest.raises(ValueError):
        workbook_preseason_prior(last_rating=0, talent_z=0,
                                 returning_z=0, new_head_coach=1)
