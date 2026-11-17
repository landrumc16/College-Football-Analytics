"""Research-only rolling recency weights; never applied to production ratings.

Weights are assigned by each team's completed-game order, not global week.
The newest three games have exactly equal individual weights.
"""
from math import isfinite


def rolling_tier_weights(game_count: int, *, early: float = 1.0,
                         middle: float = 1.5, recent: float = 2.0) -> tuple[float, ...]:
    """Return normalized chronological weights, oldest to newest.

    Last three games: recent tier. Previous three: middle tier.
    All remaining earlier games: early tier. For fewer than three
    games all available games share equal recent weight.
    """
    if isinstance(game_count, bool) or not isinstance(game_count, int) or game_count < 0:
        raise ValueError("game_count must be a nonnegative integer")
    values = (early, middle, recent)
    if any(not isinstance(v, (float, int)) or isinstance(v, bool)
           or not isfinite(v) or v <= 0 for v in values):
        raise ValueError("tier weights must be finite and positive")
    raw = [recent if index >= game_count - 3 else
           middle if index >= game_count - 6 else early
           for index in range(game_count)]
    total = sum(raw)
    return tuple(v / total for v in raw) if total else ()


def team_game_weights(games: list, team: str, *, early: float = 1.0,
                      middle: float = 1.5, recent: float = 2.0) -> dict[int, float]:
    """Map input-game indices to a team's weights.

    Caller must supply completed games in chronological order. Identical
    weights apply to the last three appearances even across bye weeks.
    """
    indices = [i for i, g in enumerate(games)
               if g.home == team or g.away == team]
    weights = rolling_tier_weights(len(indices), early=early,
                                   middle=middle, recent=recent)
    return dict(zip(indices, weights))
