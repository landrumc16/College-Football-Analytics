"""Strict champion promotion decision from verified paired historical forecasts.

Statistical uncertainty is reported, not mistaken for guaranteed improvement.
A challenger needs at least two held-out seasons and 100 matched games.
"""
from math import sqrt
from .historical import validate_unique_games
from .historical_evaluation import ArchivedForecast


def promotion_gate(games, champion, challenger, *, min_games=100, min_seasons=2):
    validate_unique_games(games)
    def index(rows):
        out = {}
        for row in rows:
            if not isinstance(row, ArchivedForecast):
                raise ValueError("Forecasts must carry validated archive provenance")
            key = (row.season, row.game_id)
            if key in out:
                raise ValueError("Duplicate archived forecast")
            out[key] = row
        return out
    a, b = index(champion), index(challenger)
    deltas, seasons = [], set()
    excluded = {"ineligible": 0, "unmatched": 0, "not_verified_pregame": 0}
    for game in games:
        if not game.eligible_fbs_accuracy:
            excluded["ineligible"] += 1
            continue
        key = (game.season, game.game_id)
        if key not in a or key not in b:
            excluded["unmatched"] += 1
            continue
        left, right = a[key], b[key]
        if not all(game.verified_pregame(f.generated_at, f.input_retrieved_at)
                   for f in (left, right)):
            excluded["not_verified_pregame"] += 1
            continue
        y = int(game.home_score > game.away_score)
        deltas.append((right.home_win_probability - y) ** 2 -
                      (left.home_win_probability - y) ** 2)
        seasons.add(game.season)
    n = len(deltas)
    mean = sum(deltas) / n if n else None
    se = (sqrt(sum((d - mean) ** 2 for d in deltas) / (n * (n - 1)))
          if n > 1 else None)
    upper = mean + 1.96 * se if se is not None else None
    sufficient = n >= min_games and len(seasons) >= min_seasons
    return {"matched_games": n, "heldout_seasons": len(seasons),
            "brier_delta": mean, "brier_delta_standard_error": se,
            "upper_95_percent_normal_bound": upper,
            "eligible": sufficient and upper is not None and upper < 0,
            "excluded": excluded,
            "decision": ("eligible_for_release_review" if sufficient and upper is not None and upper < 0
                         else "retain_champion"),
            "note": "Normal bound assumes independent games; inspect season clustering and chronology before promotion."}
