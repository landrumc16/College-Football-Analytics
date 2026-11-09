"""Retrospective, schedule-adjusted season rating research from audited games.

These ratings use final results and are NOT pregame forecasts or an independently
validated comparable multi-season program-strength scale. No publication gate is
implied by generating this research artifact.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite

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
    def kickoff_utc(game: dict) -> datetime:
        return datetime.fromisoformat(game["kickoff"].replace("Z", "+00:00")).astimezone(timezone.utc)

    ordered = sorted(games, key=lambda g: (kickoff_utc(g), g["game_id"]))
    index = 0
    while index < len(ordered):
        kickoff = kickoff_utc(ordered[index])
        batch = []
        while index < len(ordered) and kickoff_utc(ordered[index]) == kickoff:
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


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate research-only retrospective season Elo ratings")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.input.glob("games_20*.json"))
    if not paths:
        parser.error("No historical game extracts found")
    seasons = [
        retrospective_season_ratings(json.loads(path.read_text()),
                                     int(path.stem.removeprefix("games_")))
        for path in paths
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "status": "retrospective_schedule_adjusted_research_only",
        "comparable_across_seasons_verified": False,
        "program_rankings_publishable": False,
        "seasons": seasons,
    }, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
