"""Auditable opponent-strength context for retrospective team-season research.

Uses season Elo ratings after all games. This is descriptive hindsight,
not a time-safe pregame strength of schedule or publication-ready program rank.
"""
from __future__ import annotations

from collections import defaultdict
from math import isfinite

from .v4_source_integrity import validate_season_games


def season_schedule_context(games: list[dict], season_ratings: dict, season: int) -> dict:
    validate_season_games(games, season)
    if season_ratings.get("season") != season or season_ratings.get("status") != "retrospective_schedule_adjusted_research_only":
        raise ValueError("Ratings must match the retrospective source season")
    ratings = {}
    for row in season_ratings["teams"]:
        team, rating = row["team"], row["rating"]
        if team in ratings or not isinstance(rating, (float, int)) or isinstance(rating, bool) or not isfinite(rating):
            raise ValueError("Duplicate or invalid season rating")
        ratings[team] = float(rating)
    rows = defaultdict(lambda: {"fbs_opponent_ratings": [], "other_opponents": 0,
                                "quality_wins": 0, "quality_losses": 0})
    for game in games:
        for side, other in (("home", "away"), ("away", "home")):
            if game[f"{side}_division"] != "FBS":
                continue
            team = game[side]
            if team not in ratings:
                raise ValueError("Missing FBS team rating")
            opponent = game[other]
            if game[f"{other}_division"] != "FBS":
                rows[team]["other_opponents"] += 1
                continue
            if opponent not in ratings:
                raise ValueError("Missing FBS opponent rating")
            rows[team]["fbs_opponent_ratings"].append(ratings[opponent])
            if ratings[opponent] > 1500:
                if game[f"{side}_score"] > game[f"{other}_score"]:
                    rows[team]["quality_wins"] += 1
                elif game[f"{side}_score"] < game[f"{other}_score"]:
                    rows[team]["quality_losses"] += 1
    output = []
    for team in sorted(ratings):
        data = rows[team]
        opponents = data["fbs_opponent_ratings"]
        output.append({
            "team": team,
            "fbs_opponent_count": len(opponents),
            "other_opponent_count": data["other_opponents"],
            "mean_fbs_opponent_elo": round(sum(opponents) / len(opponents), 6) if opponents else None,
            "wins_vs_above_1500_fbs": data["quality_wins"],
            "losses_vs_above_1500_fbs": data["quality_losses"],
        })
    return {
        "status": "retrospective_opponent_context_only",
        "season": season,
        "pregame_available": False,
        "comparable_across_seasons_verified": False,
        "quality_threshold": "opponent final retrospective Elo > 1500; research convention only",
        "teams": output,
    }


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rating_report = json.loads(args.ratings.read_text())
    rating_seasons = {r["season"]: r for r in rating_report["seasons"]}
    reports = []
    for path in sorted(args.input.glob("games_20*.json")):
        season = int(path.stem.removeprefix("games_"))
        if season not in rating_seasons:
            raise ValueError(f"Missing season ratings: {season}")
        reports.append(season_schedule_context(json.loads(path.read_text()), rating_seasons[season], season))
    if len(reports) != len(rating_seasons):
        raise ValueError("Historical seasons and rating seasons differ")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "status": "retrospective_opponent_context_only",
        "pregame_available": False,
        "program_rankings_publishable": False,
        "seasons": reports,
    }, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
