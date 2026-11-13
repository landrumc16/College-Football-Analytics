"""Prepare national historical research and actionable identity-review diagnostics.

Consumes existing downloaded artifacts; never treats provenance formatting as
independent source verification and never publishes grades.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.build_v5_poll_history import build_poll_history
from src.cfb_analytics.v5_program_trajectory import trajectory_measurements


def prepare(records: dict, snapshots: list[dict], mapping: dict[str, str],
            *, latest_completed_season: int, source: str) -> dict:
    trajectory = trajectory_measurements(
        records, latest_completed_season=latest_completed_season,
        source=source, source_reviewed=False,
    )
    start = latest_completed_season - 9
    poll_rows = build_poll_history(snapshots, mapping, start, latest_completed_season)
    missing: dict[str, list[str]] = {}
    observed: dict[str, set[str]] = {}
    for snapshot in snapshots:
        year = snapshot["season"]
        for label, entries in snapshot["snapshots"].items():
            for entry in entries:
                team_id = str(entry["team_id"])
                if team_id not in mapping:
                    missing.setdefault(team_id, []).append(f"{year}:{label}")
                observed.setdefault(team_id, set()).add(f"{year}:{label}")
    return {
        "schema_version": 1,
        "status": "research_only_requires_independent_source_and_identity_review",
        "publishable": False,
        "latest_completed_season": latest_completed_season,
        "source": source,
        "coverage": {
            "trajectory_complete_programs": len(trajectory),
            "mapped_poll_programs": len(mapping),
            "ranked_espn_ids": len(observed),
            "unmapped_ranked_espn_ids": len(missing),
            "poll_observations": len(poll_rows),
        },
        "unmapped_ranked_team_ids": {
            key: sorted(set(value)) for key, value in
            sorted(missing.items(), key=lambda item: int(item[0]))
        },
        "trajectory": trajectory,
        "poll_history": poll_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team-season-records", type=Path, required=True)
    parser.add_argument("--poll-snapshots", type=Path, required=True)
    parser.add_argument("--team-ids", type=Path, required=True)
    parser.add_argument("--results-source", required=True)
    parser.add_argument("--latest-completed-season", type=int, default=2025)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    snapshots = [
        load(args.poll_snapshots / f"poll_snapshots_{year}.json")
        for year in range(args.latest_completed_season - 9, args.latest_completed_season + 1)
    ]
    report = prepare(
        load(args.team_season_records), snapshots, load(args.team_ids),
        latest_completed_season=args.latest_completed_season,
        source=args.results_source,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")


if __name__ == "__main__":
    main()
