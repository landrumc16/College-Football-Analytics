"""Season-level recruiting expectations fitted only on earlier completed seasons.

Simple ridge-regularized regression predicts win rate from recruiting points.
No retrospective as-of claim: caller must independently verify each training
feature's publication timing before using results for prediction backtests.
"""
from math import isfinite


def walkforward_recruiting_baseline(rows, *, min_train_seasons=3, ridge=1.0):
    if ridge <= 0 or not isfinite(ridge):
        raise ValueError("Positive ridge penalty required")
    seen = set()
    for row in rows:
        key = (row["season"], row["team"])
        if key in seen:
            raise ValueError("Duplicate team-season")
        seen.add(key)
        if type(row["season"]) is not int or not isinstance(row["team"], str) or not row["team"].strip():
            raise ValueError("Invalid team-season")
        points, wins, games = row["recruiting_points"], row["actual_wins"], row["games_played"]
        if (type(points) not in (int, float) or not isfinite(points) or points < 0
                or type(wins) is not int or type(games) is not int or games <= 0
                or not 0 <= wins <= games):
            raise ValueError("Invalid recruiting or completed season record")
    seasons = sorted({r["season"] for r in rows})
    output = []
    for season in seasons:
        train = [r for r in rows if r["season"] < season]
        if len({r["season"] for r in train}) < min_train_seasons:
            continue
        # Weighted ridge regression with a free intercept; use wins/games
        # rather than total wins so different schedule lengths are comparable.
        weight = sum(r["games_played"] for r in train)
        xbar = sum(r["recruiting_points"] * r["games_played"] for r in train) / weight
        ybar = sum(r["actual_wins"] for r in train) / weight
        numerator = sum(r["games_played"] * (r["recruiting_points"]-xbar)
                        * (r["actual_wins"]/r["games_played"]-ybar) for r in train)
        denominator = ridge + sum(r["games_played"] * (r["recruiting_points"]-xbar)**2 for r in train)
        slope = numerator / denominator
        for row in rows:
            if row["season"] != season:
                continue
            p = max(0.0, min(1.0, ybar + slope * (row["recruiting_points"]-xbar)))
            output.append({"season": season, "team": row["team"],
                           "expected_wins": p * row["games_played"],
                           "actual_wins": row["actual_wins"],
                           "games_played": row["games_played"],
                           "train_through_season": season - 1,
                           "historical_asof_verified": False})
    return sorted(output, key=lambda r: (r["season"], r["team"]))
