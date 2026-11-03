"""Research-only preseason prior reproduced from the original Google workbook.

Coefficients: 'Model Settings'!B17:B21 in CFB Ranks 09.09.2026.
Fitted on 2016-2025 data per workbook; NOT independently validated here.
Do not apply to the production model without chronological paired validation.
"""
from math import isfinite

INTERCEPT = 0.9847
LAST_RATING_WEIGHT = 0.4569
TALENT_Z_WEIGHT = 4.0926
RETURNING_Z_WEIGHT = 1.5987
NEW_HEAD_COACH_WEIGHT = -2.9411
DEFAULT_LAST_RATING = -12.0


def workbook_preseason_prior(*, last_rating, talent_z, returning_z, new_head_coach):
    """Return a prior only with complete, dated upstream feature evidence.

    A newly promoted FCS program may explicitly supply DEFAULT_LAST_RATING;
    missing talent or returning production is never silently replaced with 0.
    """
    values = (last_rating, talent_z, returning_z)
    if any(type(v) not in (float, int) or not isfinite(v) for v in values):
        raise ValueError("Complete finite rating, talent, and production inputs required")
    if type(new_head_coach) is not bool:
        raise ValueError("New head coach must be a verified boolean")
    return (INTERCEPT + LAST_RATING_WEIGHT * last_rating
            + TALENT_Z_WEIGHT * talent_z
            + RETURNING_Z_WEIGHT * returning_z
            + NEW_HEAD_COACH_WEIGHT * int(new_head_coach))
