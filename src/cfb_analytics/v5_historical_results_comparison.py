"""Compare independently sourced historical FBS season records before promotion.

The comparison is fail-closed: disagreement, missing teams, and missing seasons
are exceptions, never silently treated as corroborated records.
"""
from __future__ import annotations


def _index(archive: dict) -> dict[tuple[int, str], tuple[int, int]]:
    if not isinstance(archive, dict) or not isinstance(archive.get("seasons"), list):
        raise ValueError("Historical archive must contain seasons")
    result = {}
    years = set()
    for season in archive["seasons"]:
        year = season.get("season")
        if type(year) is not int or year in years:
            raise ValueError("Invalid or duplicate season")
        years.add(year)
        for row in season.get("teams", []):
            team = row.get("team")
            wins, losses = row.get("fbs_wins"), row.get("fbs_losses")
            if not isinstance(team, str) or not team.strip():
                raise ValueError("Invalid team identity")
            if any(type(x) is not int or x < 0 for x in (wins, losses)):
                raise ValueError("Invalid FBS win-loss totals")
            key = (year, team)
            if key in result:
                raise ValueError("Duplicate team-season")
            result[key] = (wins, losses)
    return result


def compare_historical_results(primary: dict, independent: dict, *,
                               primary_source: str, independent_source: str) -> dict:
    """Return accepted intersection and explicit unresolved exceptions.

    The caller must independently establish that these URLs represent genuinely
    different underlying data providers, not mirrors of the same feed.
    """
    if not all(isinstance(s, str) and s.startswith("https://")
               for s in (primary_source, independent_source)):
        raise ValueError("Two source URLs required")
    if primary_source == independent_source:
        raise ValueError("Two distinct sources required")
    a, b = _index(primary), _index(independent)
    accepted, exceptions = [], []
    for year, team in sorted(a.keys() | b.keys()):
        left, right = a.get((year, team)), b.get((year, team))
        if left is not None and right is not None and left == right:
            accepted.append({"season": year, "team": team,
                             "fbs_wins": left[0], "fbs_losses": left[1]})
        else:
            exceptions.append({"season": year, "team": team,
                               "primary": list(left) if left is not None else None,
                               "independent": list(right) if right is not None else None,
                               "reason": "missing_source" if left is None or right is None
                                         else "conflicting_record"})
    return {"schema_version": 1, "status": "comparison_only_requires_independence_review",
            "primary_source": primary_source, "independent_source": independent_source,
            "source_independence_attested": False,
            "accepted_matching_records": accepted, "exceptions": exceptions,
            "matching_count": len(accepted), "exception_count": len(exceptions)}
