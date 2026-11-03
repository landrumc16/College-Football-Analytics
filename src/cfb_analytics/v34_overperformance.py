"""Research-only recruiting expectation residuals from complete, dated seasons.

A residual is descriptive, not a causal measure of coaching or scouting skill.
Never rank a team with missing talent inputs as if its talent were zero.
"""
from collections import defaultdict
from math import isfinite


def talent_overperformance(rows, *, min_seasons=3):
    """Rank season-level actual-minus-expected results with explicit coverage.

    Each row: season, team, recruiting_expectation_wins, actual_wins,
    source, expectation_published_at, season_start_at.
    Expectations must have been published strictly before the season started.
    """
    from .historical import utc_instant
    seen = set()
    groups = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Expected season record")
        key = (row.get("season"), row.get("team"))
        if key in seen:
            raise ValueError("Duplicate team season")
        seen.add(key)
        if type(key[0]) is not int or not isinstance(key[1], str) or not key[1].strip():
            raise ValueError("Invalid season/team")
        if not isinstance(row.get("source"), str) or not row["source"].strip():
            raise ValueError("Missing expectation provenance")
        published = utc_instant(row.get("expectation_published_at"))
        start = utc_instant(row.get("season_start_at"))
        if published is None or start is None or published >= start:
            raise ValueError("Expectation must be dated before season start")
        expected, actual = row.get("recruiting_expectation_wins"), row.get("actual_wins")
        if (type(expected) not in (int, float) or not isfinite(expected)
                or type(actual) is not int or actual < 0 or expected < 0):
            raise ValueError("Missing or invalid wins")
        games = row.get("games_played")
        if type(games) is not int or games <= 0 or actual > games or expected > games:
            raise ValueError("Season games must bound expected and actual wins")
        groups[key[1]].append((key[0], actual - expected))
    output = []
    for team, values in groups.items():
        if len(values) < min_seasons:
            continue
        values.sort()
        output.append({"team": team, "seasons": len(values),
                       "first_season": values[0][0], "last_season": values[-1][0],
                       "average_wins_above_recruiting_expectation":
                       sum(v for _, v in values) / len(values)})
    return sorted(output, key=lambda r: (-r["average_wins_above_recruiting_expectation"], r["team"]))
