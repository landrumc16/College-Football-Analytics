"""Build one consistent descriptive dataset for program comparison and team tiles.

The inputs must be sourced historical records. Missing data stays missing;
this export never fabricates a ten-season history or predictive validation.
"""
from __future__ import annotations

from .v4_hype_index import historical_hype
from .v4_program_rankings import rank_programs
from .v4_program_trajectory import program_trajectories


def build_program_intelligence(strength_rows: list[dict], poll_rows: list[dict],
                               latest_completed_season: int) -> dict:
    rankings = rank_programs(strength_rows, latest_completed_season)
    trajectories = program_trajectories(strength_rows, latest_completed_season)
    hype = historical_hype(poll_rows, latest_completed_season)
    by_team = {}
    for record in rankings["programs"]:
        by_team[record["team"]] = {
            "team": record["team"], "program_rankings": record["windows"],
            "trajectory": None, "hype": {},
        }
    for record in trajectories["programs"]:
        by_team.setdefault(record["team"], {
            "team": record["team"], "program_rankings": None, "trajectory": None, "hype": {},
        })["trajectory"] = {
            "long_term": record["long_term"], "medium_term": record["medium_term"], "recent": record["recent"],
        }
    for record in hype["program_polls"]:
        by_team.setdefault(record["team"], {
            "team": record["team"], "program_rankings": None, "trajectory": None, "hype": {},
        })["hype"][record["poll"]] = {
            key: value for key, value in record.items() if key not in ("team", "poll")
        }
    # Preserve independently sourced season observations for a real time-series
    # chart; never interpolate or replace missing seasons with aggregate ranks.
    season_history = {}
    for row in strength_rows:
        season_history.setdefault(row["team"], []).append({
            "season": row["season"], "strength": row["strength"], "source": row["source"],
        })
    for team, records in season_history.items():
        if team in by_team:
            by_team[team]["season_strength_history"] = sorted(
                records, key=lambda record: record["season"]
            )
    return {
        "schema_version": 1,
        "status": "descriptive_only",
        "latest_completed_season": latest_completed_season,
        "predictive_validation": False,
        "coverage": {
            "programs_with_strength_history": len(rankings["programs"]),
            "program_poll_records": len(hype["program_polls"]),
        },
        "programs": sorted(by_team.values(), key=lambda record: record["team"]),
    }
