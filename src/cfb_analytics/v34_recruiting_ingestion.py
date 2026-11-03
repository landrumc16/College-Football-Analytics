"""Normalize CFBD recruiting-team season data without inventing historical availability.

A retrieval timestamp is NOT the original publication timestamp. Therefore
these records can support descriptive research but not retrospective forecasts
unless independent as-of evidence is provided.
"""
from math import isfinite
from .historical import utc_instant


def normalize_recruiting_classes(records, *, retrieved_at, source="CFBD recruiting/teams"):
    if utc_instant(retrieved_at) is None:
        raise ValueError("Retrieval timestamp must be timezone-aware")
    output = {}
    for row in records:
        year, team = row.get("year"), row.get("team")
        if type(year) is not int or not isinstance(team, str) or not team.strip():
            raise ValueError("Recruiting class requires year and team")
        key = (year, team)
        if key in output:
            raise ValueError("Duplicate recruiting class")
        points = row.get("points")
        rank = row.get("rank")
        if type(points) not in (float, int) or not isfinite(points) or points < 0:
            raise ValueError("Missing or invalid recruiting points")
        if rank is not None and (type(rank) is not int or rank < 1):
            raise ValueError("Invalid recruiting class rank")
        output[key] = {"season": year, "team": team, "recruiting_points": points,
                       "recruiting_rank": rank, "source": source,
                       "retrieved_at": retrieved_at,
                       "historical_asof_verified": False}
    return [output[k] for k in sorted(output)]
