"""Reproducible team-season results from verified historical FBS-participant games.

Descriptive only: this is not an opponent-adjusted strength rating or a
historical pregame feature archive. Team names retain source identity.
"""
from __future__ import annotations

from collections import defaultdict

from .v4_source_integrity import validate_season_games


def team_season_records(games: list[dict], season: int) -> dict:
    integrity = validate_season_games(games, season)
    teams = defaultdict(lambda: {
        "wins": 0, "losses": 0, "ties": 0,
        "fbs_wins": 0, "fbs_losses": 0, "fbs_ties": 0,
        "other_wins": 0, "other_losses": 0, "other_ties": 0,
        "points_for": 0, "points_against": 0,
    })
    for game in games:
        for side, opponent in (("home", "away"), ("away", "home")):
            if game[f"{side}_division"] != "FBS":
                continue
            team = game[side]
            stats = teams[team]
            ours, theirs = game[f"{side}_score"], game[f"{opponent}_score"]
            result = "wins" if ours > theirs else "losses" if ours < theirs else "ties"
            bucket = "fbs_" if game[f"{opponent}_division"] == "FBS" else "other_"
            stats[result] += 1
            stats[bucket + result] += 1
            stats["points_for"] += ours
            stats["points_against"] += theirs
    return {
        "status": "retrospective_descriptive_results_only",
        "season": season,
        "game_count": integrity["games"],
        "team_count": len(teams),
        "opponent_adjusted": False,
        "pregame_available": False,
        "teams": [{"team": team, **teams[team]} for team in sorted(teams)],
    }
