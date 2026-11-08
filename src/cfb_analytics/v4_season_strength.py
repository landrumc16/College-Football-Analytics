"""Retrospective, schedule-adjusted season rating research from audited games.

These ratings use final results and are NOT pregame forecasts or an independently
validated comparable multi-season program-strength scale. No publication gate is
implied by generating this research artifact.
"""
from __future__ import annotations

from collections import defaultdict
from math import exp, isfinite

from .v4_source_integrity import validate_season_games


def retrospective_season_ratings(games: list[dict], season: int, *,
                                 k_factor: float = 24.0,
                                 home_advantage: float = 55.0) -> dict:
    if not isfinite(k_factor) or k_factor <= 0:
        raise ValueError("k_factor must be positive and finite")
    if not isfinite(home_advantage):
        raise ValueError("home_advantage must be finite")
    validate_season_games(games, season)
    ratings = defaultdict(lambda: 1500.0)
    counts = defaultdict(int)
    # All games are sorted by actual kickoff. Simultaneous games must be
    # predicted from the same pre-batch ratings; final scores update only after.
    ordered = sorted(games, key=lambda g: (g["kickoff"], g["game_id"]))
    index = 0
    while index < len(ordered):
        kickoff = ordered[index]["kickoff"]
        batch = []
        while index < len(ordered) and ordered[index]["kickoff"] == kickoff:
            batch.append(ordered[index])
            index += 1
        deltas = defaultdict(float)
        for game in batch:
            home, away = game["home"], game["away"]
            home_rating, away_rating = ratings[home], ratings[away]
            venue = 0.0 if game.get("neutral_site") is True else home_advantage
            expected = 1.0 / (1.0 + 10.0 ** ((away_rating - home_rating - venue) / 400.0))
            outcome = 1.0 if game["home_score"] > game["away_score"] else (
                0.0 if game["home_score"] < game["away_score"] else 0.5
            )
            delta = k_factor * (outcome - expected)
            deltas[home] += delta
            deltas[away] -= delta
            counts[home] += 1
            counts[away] += 1
        for team, delta in deltas.items():
            ratings[team] += delta
    fbs = {g[side] for g in games for side in ("home", "away")
           if g[f"{side}_division"] == "FBS"}
    return {
        "status": "retrospective_schedule_adjusted_research_only",
        "season": season,
        "method": "Within-season Elo, equal 1500 starts, K=24 default, home advantage=55 default",
        "comparable_across_seasons_verified": False,
        "pregame_archive": False,
        "predictive_validation": False,
        "teams": [{"team": team, "rating": round(ratings[team], 6),
                   "games": counts[team]} for team in sorted(fbs)],
    }
