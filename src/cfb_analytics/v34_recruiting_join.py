"""Join actual season records to independently dated preseason expectations.

No fabricated expected wins, no post-season recruiting values, no incomplete
season treated as final. The caller supplies an explicit season-completion set.
"""
from .historical import utc_instant
from .v34_overperformance import talent_overperformance


def evaluate_recruiting_residuals(actual_records, expectations, *, completed_seasons,
                                  min_seasons=3):
    actual = {}
    for row in actual_records:
        key = (row["season"], row["team"])
        if key in actual:
            raise ValueError("Duplicate actual team-season")
        actual[key] = row
    seen, matched = set(), []
    missing_actual = 0
    incomplete = 0
    for row in expectations:
        key = (row["season"], row["team"])
        if key in seen:
            raise ValueError("Duplicate expectation team-season")
        seen.add(key)
        if row["season"] not in completed_seasons:
            incomplete += 1
            continue
        record = actual.get(key)
        if record is None:
            missing_actual += 1
            continue
        if utc_instant(row.get("expectation_published_at")) is None:
            raise ValueError("Expectation needs timezone-aware publication date")
        matched.append({**row, "actual_wins": record["actual_wins"],
                        "games_played": record["games_played"]})
    return {"rankings": talent_overperformance(matched, min_seasons=min_seasons),
            "matched_team_seasons": len(matched),
            "excluded_incomplete_season": incomplete,
            "excluded_missing_actual": missing_actual,
            "scope": "descriptive recruiting expectation residuals, not causal coaching effects"}
