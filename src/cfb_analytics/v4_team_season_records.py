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


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Build descriptive team-season records from audited historical games")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.input.glob("games_20*.json"))
    if not files:
        parser.error("No historical game extracts found")
    reports = []
    for path in files:
        season = int(path.stem.removeprefix("games_"))
        reports.append(team_season_records(json.loads(path.read_text()), season))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "status": "retrospective_descriptive_results_only",
        "opponent_adjusted": False,
        "pregame_available": False,
        "seasons": reports,
    }, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
