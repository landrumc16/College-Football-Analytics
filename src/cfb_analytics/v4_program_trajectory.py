"""Descriptive program trajectory derived from the shared historical strength scale.

The input is a verified, comparable, opponent-adjusted strength per team-season.
This module does not infer missing observations or make predictive claims.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite


def program_trajectories(rows: list[dict], latest_season: int, *,
                         long_window: int = 10, medium_window: int = 5, recent_window: int = 3,
                         steady_threshold: float = 1.0,
                         rapid_threshold: float = 3.0) -> dict:
    """Return descriptive trend and momentum in strength units per season.

    A full ten-year history is required for long-term classification; a full
    three-year history is required for recent momentum. Classification uses
    the slope of least-squares linear fit, not the difference between endpoints.
    Thresholds are explicit and must be calibrated for the source strength scale.
    """
    if not isinstance(latest_season, int) or isinstance(latest_season, bool):
        raise ValueError("Invalid latest season")
    if long_window < 2 or recent_window < 2 or not recent_window <= medium_window <= long_window:
        raise ValueError("Invalid trend windows")
    if not (0 <= steady_threshold < rapid_threshold) or not all(
        isfinite(v) for v in (steady_threshold, rapid_threshold)
    ):
        raise ValueError("Invalid classification thresholds")
    histories = defaultdict(dict)
    for row in rows:
        if not all(key in row for key in ("team", "season", "strength", "source")):
            raise ValueError("Missing required season fields")
        team, year, value, source = (row[key] for key in ("team", "season", "strength", "source"))
        if not isinstance(team, str) or not team.strip() or not isinstance(source, str) or not source.strip():
            raise ValueError("Invalid team or source")
        if not isinstance(year, int) or isinstance(year, bool) or year > latest_season:
            raise ValueError("Invalid completed season")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
            raise ValueError("Invalid strength")
        if year in histories[team]:
            raise ValueError("Duplicate team-season")
        histories[team][year] = float(value)

    def slope(values: list[float]) -> float:
        n = len(values)
        center = (n - 1) / 2
        return sum((i - center) * v for i, v in enumerate(values)) / sum(
            (i - center) ** 2 for i in range(n)
        )

    def classification(value: float) -> str:
        if value >= rapid_threshold:
            return "rapidly_rising"
        if value >= steady_threshold:
            return "steadily_improving"
        if value <= -rapid_threshold:
            return "rapidly_declining"
        if value <= -steady_threshold:
            return "steadily_declining"
        return "stable"

    programs = []
    for team in sorted(histories):
        history = histories[team]
        result = {"team": team}
        for window, key in ((long_window, "long_term"), (medium_window, "medium_term"), (recent_window, "recent")):
            years = list(range(latest_season - window + 1, latest_season + 1))
            available = [year for year in years if year in history]
            rate = slope([history[year] for year in years]) if len(available) == window else None
            result[key] = {
                "window": window,
                "seasons_available": len(available),
                "slope_per_season": rate,
                "classification": classification(rate) if rate is not None else "insufficient_data",
            }
        programs.append(result)
    return {
        "status": "descriptive_only",
        "latest_completed_season": latest_season,
        "predictive_validation": False,
        "thresholds_strength_units_per_season": {
            "steady": steady_threshold, "rapid": rapid_threshold,
        },
        "programs": programs,
    }
