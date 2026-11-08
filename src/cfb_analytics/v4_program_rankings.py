"""Descriptive multi-season program rankings from externally verified season strengths.

Inputs are *already opponent-adjusted* season-level ratings on one comparable
scale. This module does not estimate schedule strength, infer missing seasons,
or claim prediction accuracy. The source pipeline owns those responsibilities.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite


def rank_programs(rows: list[dict], latest_season: int, windows: tuple[int, ...] = (10, 5, 3)) -> dict:
    """Rank programs within each trailing completed-season window.

    Each row requires team, season, strength and a nonempty source. A team must
    have every season in a window to receive a rank for that window. Rank 1 is
    strongest; tied scores share a competition rank. Missing coverage is null.
    """
    if not isinstance(latest_season, int) or isinstance(latest_season, bool):
        raise ValueError("latest_season must be an integer")
    if not windows or any(not isinstance(w, int) or isinstance(w, bool) or w < 1 for w in windows):
        raise ValueError("windows must contain positive integers")
    if len(set(windows)) != len(windows):
        raise ValueError("Duplicate windows")
    by_team = defaultdict(dict)
    sources_by_team = defaultdict(dict)
    for row in rows:
        if not all(k in row for k in ("team", "season", "strength", "source")):
            raise ValueError("Missing required program season fields")
        team, season, score, source = (row[k] for k in ("team", "season", "strength", "source"))
        if not isinstance(team, str) or not team.strip() or not isinstance(source, str) or not source.strip():
            raise ValueError("Team and source must be nonempty strings")
        if not isinstance(season, int) or isinstance(season, bool) or season > latest_season:
            raise ValueError("Season must be completed and no later than latest_season")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not isfinite(score):
            raise ValueError("Strength must be a finite numeric value")
        if season in by_team[team]:
            raise ValueError("Duplicate team-season strength")
        by_team[team][season] = float(score)
        sources_by_team[team][season] = source.strip()
    output = {team: {"team": team, "windows": {}} for team in sorted(by_team)}
    for window in windows:
        seasons = range(latest_season - window + 1, latest_season + 1)
        scores = {}
        for team, history in by_team.items():
            present = [year for year in seasons if year in history]
            score = sum(history[year] for year in present) / window if len(present) == window else None
            output[team]["windows"][str(window)] = {
                "rank": None, "strength": score, "seasons_available": len(present),
                "seasons_required": window,
                "years": list(present),
                "sources": [{"season": year, "source": sources_by_team[team][year]} for year in present],
                "publishable": score is not None,
            }
            if score is not None:
                scores[team] = score
        last_score = None
        last_rank = None
        for position, (team, score) in enumerate(sorted(scores.items(), key=lambda item: (-item[1], item[0])), 1):
            rank = last_rank if score == last_score else position
            output[team]["windows"][str(window)]["rank"] = rank
            last_score, last_rank = score, rank
    return {
        "status": "descriptive_only",
        "latest_completed_season": latest_season,
        "windows": list(windows),
        "methodology": "Equal-weight mean of independently sourced, comparable opponent-adjusted season strengths; full window required",
        "predictive_validation": False,
        "programs": list(output.values()),
    }
