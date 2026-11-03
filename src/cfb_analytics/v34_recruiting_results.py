"""Research-only team-season recruiting strength versus observed season results.

This reports associations, not causal player-development or coaching effects.
Historical recruiting snapshots must not be repurposed as archived forecasts.
"""
from collections import defaultdict
from math import isfinite


def recruiting_vs_results(classes, actual_records, *, completed_seasons, min_seasons=3):
    lookup = {}
    for row in actual_records:
        key = (row["season"], row["team"])
        if key in lookup:
            raise ValueError("Duplicate actual season")
        lookup[key] = row
    seen = set()
    grouped = defaultdict(list)
    excluded = {"incomplete_season": 0, "missing_actual": 0}
    for row in classes:
        key = (row["season"], row["team"])
        if key in seen:
            raise ValueError("Duplicate recruiting class")
        seen.add(key)
        if row["season"] not in completed_seasons:
            excluded["incomplete_season"] += 1
            continue
        actual = lookup.get(key)
        if actual is None:
            excluded["missing_actual"] += 1
            continue
        points = row.get("recruiting_points")
        if type(points) not in (float, int) or not isfinite(points) or points < 0:
            raise ValueError("Recruiting points must be finite and nonnegative")
        if type(actual.get("actual_wins")) is not int or type(actual.get("games_played")) is not int or not (0 <= actual["actual_wins"] <= actual["games_played"]):
            raise ValueError("Invalid season record")
        if not row.get("source") or not row.get("retrieved_at"):
            raise ValueError("Recruiting source and retrieval provenance required")
        grouped[row["team"]].append((row["season"], points, actual["actual_wins"], actual["games_played"]))
    teams = []
    for team, values in grouped.items():
        if len(values) < min_seasons:
            continue
        teams.append({"team": team, "seasons": len(values),
                      "average_recruiting_points": sum(v[1] for v in values)/len(values),
                      "win_rate": sum(v[2] for v in values)/sum(v[3] for v in values)})
    return {"teams": sorted(teams, key=lambda x: (-x["win_rate"], x["team"])),
            "matched_team_seasons": sum(len(v) for v in grouped.values()),
            "excluded": excluded,
            "scope": "descriptive association only; recruiting ranks are not pregame-verified"}
