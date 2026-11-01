"""Pure, testable primitives transcribed from the 2026 Google Sheets model.

The multi-pass ratings and projected-win calculations live in their own modules.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class ModelSettings:
    ridge_strength: float = 5.0
    conference_shrink: float = 1.0
    margin_cap: float = 45.0
    win_probability_scale: float = 18.0
    prior_year_weight: float = 1.0
    new_team_rating: float = -12.0
    fcs_opponent_rating: float = -26.0
    home_field_advantage: float = 3.0
    market_line_scale: float = 19.5


def adjusted_home_margin(home_score: int, away_score: int, settings: ModelSettings) -> float:
    """Matches Games!G: clamp(home-away-home edge, +/- margin cap).

    Note: the workbook applies the home edge here even for neutral-site games.
    """
    margin = home_score - away_score - settings.home_field_advantage
    return max(-settings.margin_cap, min(settings.margin_cap, margin))


def preseason_prior(
    previous_rating: float | None,
    talent_z: float | None,
    returning_production_z: float | None,
    new_head_coach: bool,
    *,
    intercept: float,
    previous_weight: float,
    talent_weight: float,
    returning_weight: float,
    coach_weight: float,
    missing_previous_rating: float,
) -> float:
    """Matches PreseasonPrior!F formula with blanks treated as zero for z/coach."""
    previous = missing_previous_rating if previous_rating is None else previous_rating
    return (intercept + previous_weight * previous
            + talent_weight * (talent_z or 0.0)
            + returning_weight * (returning_production_z or 0.0)
            + coach_weight * int(new_head_coach))


def win_probability_from_rating_gap(rating_gap: float, scale: float = 18.0) -> float:
    """Workbook logistic mapping: 1/(1+10^(-gap/scale))."""
    if not isfinite(rating_gap) or not isfinite(scale) or scale <= 0:
        raise ValueError("Expected finite rating gap and finite positive scale")
    exponent = rating_gap / scale
    if exponent >= 0:
        odds = 10.0 ** (-exponent)
        return 1.0 / (1.0 + odds)
    odds = 10.0 ** exponent
    return odds / (1.0 + odds)


def model_home_margin(home_rating: float, away_rating: float, *, neutral: bool = False,
                      home_field_advantage: float = 3.0) -> float:
    """Matches Predictions!F: home rating minus away plus optional home edge."""
    return home_rating - away_rating + (0.0 if neutral else home_field_advantage)


def market_home_win_probability(home_spread: float, scale: float = 19.5) -> float:
    """Matches Predictions!H market branch: 1/(1+10^(spread/Market_Scale)).

    A negative home spread indicates a home favorite.
    """
    return win_probability_from_rating_gap(-home_spread, scale)


def confidence_label(home_win_probability: float) -> str:
    """Matches Predictions!J thresholds."""
    if not 0.0 <= home_win_probability <= 1.0:
        raise ValueError("Probability outside [0, 1]")
    certainty = max(home_win_probability, 1 - home_win_probability)
    if certainty > 0.8:
        return "Strong"
    if certainty > 0.65:
        return "Likely"
    if certainty > 0.55:
        return "Lean"
    return "Toss-up"
