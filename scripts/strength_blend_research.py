"""Research-only season strength / recent momentum blend.

Inputs must be opponent-adjusted ratings on the same numeric scale.
This module does not alter production forecasts or rankings.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class StrengthBlend:
    season_strength: float
    recent_momentum: float | None
    combined_strength: float
    season_weight: float
    momentum_weight: float
    momentum_games: int
    direction: str


def blend_strength(
    season_strength: float,
    recent_momentum: float | None,
    *,
    momentum_games: int,
    momentum_weight: float = 0.35,
    minimum_games: int = 3,
) -> StrengthBlend:
    """Blend comparable ratings; avoid fabricated momentum on thin samples.

    Momentum is defined from ONLY the latest 3 or 4 completed games upstream.
    For fewer than three games, fall back to season strength without implying
    a separately measured momentum signal.
    """
    if not isfinite(season_strength):
        raise ValueError("season strength must be finite")
    if not 0 <= momentum_weight <= 1:
        raise ValueError("momentum weight must be in [0, 1]")
    if minimum_games != 3 or not 0 <= momentum_games <= 4:
        raise ValueError("momentum must use a 3- or 4-game window")
    if recent_momentum is not None and not isfinite(recent_momentum):
        raise ValueError("momentum must be finite")
    if momentum_games >= minimum_games and recent_momentum is None:
        raise ValueError("missing momentum rating for complete window")
    if momentum_games < minimum_games:
        return StrengthBlend(season_strength, None, season_strength, 1.0,
                             0.0, momentum_games, "insufficient_data")
    combined = ((1 - momentum_weight) * season_strength
                + momentum_weight * recent_momentum)
    delta = recent_momentum - season_strength
    direction = "rising" if delta > 0 else "declining" if delta < 0 else "steady"
    return StrengthBlend(season_strength, recent_momentum, combined,
                         1 - momentum_weight, momentum_weight,
                         momentum_games, direction)


def momentum_window(completed_games: list, *, window: int = 3) -> list:
    """Return exactly the latest completed games; caller sorts by kickoff.

    Does not include any earlier season games in the momentum sample.
    """
    if window not in (3, 4):
        raise ValueError("momentum window must be 3 or 4")
    return completed_games[-window:]
