"""Research-only program recruiting residuals from strictly heldout seasons.

A residual is actual wins minus recruiting-only expected wins, not causal
coaching, development, or scouting value. No pregame accuracy is asserted.
"""
from collections import defaultdict


def recruiting_residual_leaderboard(holdout_predictions, *, min_seasons=3):
    if type(min_seasons) is not int or min_seasons < 1:
        raise ValueError("Minimum seasons must be positive")
    grouped = defaultdict(list)
    seen = set()
    for row in holdout_predictions:
        key = (row["season"], row["team"])
        if key in seen:
            raise ValueError("Duplicate team-season")
        seen.add(key)
        if row.get("historical_asof_verified") is not False:
            raise ValueError("Explicit research-only as-of status required")
        if row["train_through_season"] >= row["season"]:
            raise ValueError("Training includes evaluation season")
        expected, actual, games = row["expected_wins"], row["actual_wins"], row["games_played"]
        if not (0 <= expected <= games and 0 <= actual <= games and games > 0):
            raise ValueError("Invalid wins or games")
        grouped[row["team"]].append((row["season"], actual - expected))
    leaders = []
    for team, values in grouped.items():
        if len(values) < min_seasons:
            continue
        leaders.append({"team": team, "heldout_seasons": len(values),
                        "average_wins_above_recruiting_baseline": sum(x[1] for x in values)/len(values),
                        "first_heldout_season": min(x[0] for x in values),
                        "last_heldout_season": max(x[0] for x in values)})
    return {"programs": sorted(leaders, key=lambda x: (-x["average_wins_above_recruiting_baseline"], x["team"])),
            "eligible_programs": len(leaders),
            "scope": "research-only recruiting residuals, not causal coaching/development rankings"}
