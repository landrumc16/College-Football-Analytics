"""Keep independent spreadsheet model probabilities separate from market-assisted display.

Reproduces Predictions!F, N, H, O and G in the original Google workbook.
This is a parity primitive, not evidence of historical predictive accuracy.
"""
from dataclasses import dataclass
from math import isfinite

from .model import (
    ModelSettings, market_home_win_probability, model_home_margin,
    win_probability_from_rating_gap,
)


@dataclass(frozen=True)
class WorkbookPrediction:
    projected_home_margin: float
    model_home_probability: float
    displayed_home_probability: float
    displayed_source: str
    displayed_winner: str


def workbook_prediction(
    home: str,
    away: str,
    home_rating: float,
    away_rating: float,
    *,
    neutral: bool = False,
    closing_home_spread: float | None = None,
    settings: ModelSettings = ModelSettings(),
) -> WorkbookPrediction:
    if not home or not away or home == away:
        raise ValueError("Distinct named teams required")
    if not isfinite(home_rating) or not isfinite(away_rating):
        raise ValueError("Ratings must be finite")
    if closing_home_spread is not None and not isfinite(closing_home_spread):
        raise ValueError("Closing spread must be finite")
    margin = model_home_margin(
        home_rating, away_rating, neutral=neutral,
        home_field_advantage=settings.home_field_advantage)
    independent = win_probability_from_rating_gap(
        margin, settings.win_probability_scale)
    if closing_home_spread is None:
        displayed, source = independent, "Model"
    else:
        displayed = market_home_win_probability(
            closing_home_spread, settings.market_line_scale)
        source = "Market line"
    return WorkbookPrediction(
        projected_home_margin=margin,
        model_home_probability=independent,
        displayed_home_probability=displayed,
        displayed_source=source,
        displayed_winner=home if displayed >= 0.5 else away,
    )
