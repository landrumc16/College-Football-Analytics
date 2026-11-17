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
    steady_band: float = 7.0,
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
    if minimum_games not in (3, 4) or not 0 <= momentum_games <= 4:
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
    direction = "rising" if delta > steady_band else "declining" if delta < -steady_band else "steady"
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


def calculate_strength_components(teams, chronological_games, *,
                                  window: int = 3,
                                  momentum_weight: float = 0.35,
                                  settings=None, season_ratings=None):
    """As-of opponent-adjusted season and short-window momentum ratings.

    The opponent benchmark is estimated from the full *as-of* season history,
    but a team's momentum numerator uses ONLY its last 3 or 4 games.
    Games must be completed, ordered by kickoff, and available before the
    forecast timestamp. Do not pass future games or use this in production.
    """
    from cfb_analytics.ratings import calculate_ratings
    from cfb_analytics.model import ModelSettings, adjusted_home_margin

    if window not in (3, 4):
        raise ValueError("momentum window must be 3 or 4")
    if settings is None:
        settings = ModelSettings()
    ratings = (season_ratings if season_ratings is not None else
               calculate_ratings(teams, chronological_games, settings))
    output = {}
    for team in teams:
        played = [game for game in chronological_games
                  if team.name in (game.home, game.away)]
        season = ratings[team.name].adaptive_rating
        if len(played) < window:
            output[team.name] = blend_strength(
                season, None, momentum_games=len(played),
                momentum_weight=momentum_weight, minimum_games=window)
            continue
        recent = played[-window:]
        observations = []
        for game in recent:
            home = game.home == team.name
            opponent = game.away if home else game.home
            opponent_strength = (ratings[opponent].adaptive_rating
                                 if opponent in ratings else settings.fcs_opponent_rating)
            adjusted = adjusted_home_margin(
                game.home_score, game.away_score, settings)
            observations.append(opponent_strength + (adjusted if home else -adjusted))
        # Momentum is the plain mean of the latest-window opponent-adjusted results, so no earlier game enters
        # it; the blend weight (not a hidden ridge) controls how much it moves Combined Strength.
        momentum = sum(observations) / len(observations)
        output[team.name] = blend_strength(
            season, momentum, momentum_games=len(recent),
            momentum_weight=momentum_weight, minimum_games=window)
    return output
