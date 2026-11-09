"""Source coverage inventory for V5 historical research, without publication claims.

Input arrays use the existing program-intelligence source contracts. This tool
does not infer rankings, fill missing seasons, or attest source authenticity.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from .v4_program_provenance import validate_program_sources


def historical_coverage_inventory(strength_rows: list[dict], poll_rows: list[dict],
                                  latest_season: int) -> dict:
    diagnostics = validate_program_sources(strength_rows, poll_rows, latest_season)
    strength = defaultdict(set)
    polls = defaultdict(set)
    for row in strength_rows:
        strength[row["team"]].add(row["season"])
    for row in poll_rows:
        polls[(row["team"], row["poll"])].add(row["season"])
    teams = sorted(set(strength) | {team for team, _ in polls})
    windows = (3, 5, 10)
    records = []
    for team in teams:
        available_strength = strength[team]
        by_poll = {poll: polls[(team, poll)] for poll in ("AP", "Coaches")}
        records.append({
            "team": team,
            "strength_seasons": sorted(available_strength),
            "poll_seasons": {poll: sorted(years) for poll, years in by_poll.items()},
            "windows": {
                str(window): {
                    "strength_complete": all(year in available_strength for year in range(latest_season - window + 1, latest_season + 1)),
                    "strength_missing": [year for year in range(latest_season - window + 1, latest_season + 1) if year not in available_strength],
                    "poll_complete": {poll: all(year in by_poll[poll] for year in range(latest_season - window + 1, latest_season + 1)) for poll in by_poll},
                    "poll_missing": {poll: [year for year in range(latest_season - window + 1, latest_season + 1) if year not in by_poll[poll]] for poll in by_poll},
                } for window in windows
            },
        })
    return {
        "status": "coverage_inventory_not_source_attestation",
        "latest_completed_season": latest_season,
        "provenance_diagnostics": diagnostics,
        "team_count": len(teams),
        "strength_observations": len(strength_rows),
        "poll_observations": len(poll_rows),
        "window_counts": {
            str(window): {
                "strength_complete": sum(record["windows"][str(window)]["strength_complete"] for record in records),
                "ap_complete": sum(record["windows"][str(window)]["poll_complete"]["AP"] for record in records),
                "coaches_complete": sum(record["windows"][str(window)]["poll_complete"]["Coaches"] for record in records),
            } for window in windows
        },
        "teams": records,
        "publication_authorized": False,
        "limitations": [
            "Format and coverage checks do not independently verify source authenticity",
            "Comparable opponent-adjusted strength requires independent review",
            "Preseason and final polls require independent dated source verification",
            "Coverage alone does not establish predictive validity",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strength-input", type=Path, required=True)
    parser.add_argument("--poll-input", type=Path, required=True)
    parser.add_argument("--latest-completed-season", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    strengths = json.loads(args.strength_input.read_text(encoding="utf-8"))
    polls = json.loads(args.poll_input.read_text(encoding="utf-8"))
    if not isinstance(strengths, list) or not isinstance(polls, list):
        parser.error("Both source inputs must be JSON arrays")
    report = historical_coverage_inventory(strengths, polls, args.latest_completed_season)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
