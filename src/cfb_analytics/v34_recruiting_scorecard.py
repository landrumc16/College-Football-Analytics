"""Out-of-sample diagnostics for chronological recruiting-to-wins research.

These are season-level errors, NOT pregame prediction accuracy. Historical
recruiting publication timing must be verified before any forecast use.
"""
from collections import defaultdict
from math import sqrt, isfinite


def recruiting_baseline_scorecard(predictions, *, min_seasons=2):
    seen = set()
    by_season = defaultdict(list)
    for row in predictions:
        key = (row["season"], row["team"])
        if key in seen:
            raise ValueError("Duplicate holdout team-season")
        seen.add(key)
        if row.get("historical_asof_verified") is not False:
            raise ValueError("Research scorecard requires explicit as-of status")
        if type(row.get("train_through_season")) is not int or row["train_through_season"] >= row["season"]:
            raise ValueError("Training must end before evaluation season")
        expected, actual, games = row["expected_wins"], row["actual_wins"], row["games_played"]
        if (type(expected) not in (int, float) or not isfinite(expected)
                or type(actual) is not int or type(games) is not int
                or games <= 0 or not 0 <= expected <= games or not 0 <= actual <= games):
            raise ValueError("Invalid expected or actual season wins")
        by_season[row["season"]].append(expected - actual)
    errors = [v for values in by_season.values() for v in values]
    n = len(errors)
    return {"evaluated_team_seasons": n, "heldout_seasons": len(by_season),
            "sufficient_seasons": len(by_season) >= min_seasons,
            "win_mae": sum(abs(x) for x in errors) / n if n else None,
            "win_rmse": sqrt(sum(x*x for x in errors) / n) if n else None,
            "mean_error": sum(errors) / n if n else None,
            "by_season": [{"season": year, "team_seasons": len(values),
                           "win_mae": sum(abs(v) for v in values)/len(values)}
                          for year, values in sorted(by_season.items())],
            "promotion_status": "research_only_not_pregame_verified"}
