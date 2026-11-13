"""Convert verified poll snapshots into ten-season Hype Index input.

Fail closed on missing years, duplicate identities, and unresolved team IDs.
The resulting rows remain research-only until source authenticity is reviewed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.fetch_v5_historical_polls import valid_top25


def build_poll_history(snapshots: list[dict], team_ids: dict[str, str],
                       start: int = 2016, end: int = 2025, *,
                       require_ranked_ids_mapped: bool = False) -> list[dict]:
    years = set(range(start, end + 1))
    if {item["season"] for item in snapshots} != years or len(snapshots) != len(years):
        raise ValueError("Poll snapshots must cover every requested season exactly once")
    if not team_ids or len(set(team_ids.values())) != len(team_ids) or not all(team_ids.values()):
        raise ValueError("Team mapping must contain unique nonempty canonical names")
    # Every mapped cohort program needs an observation even when unranked.
    output = []
    for item in sorted(snapshots, key=lambda row: row["season"]):
        year = item["season"]
        source = item["source_url"]
        if not source.startswith("https://") or len(item["source_sha256"]) != 64:
            raise ValueError(f"{year}: missing source provenance")
        for poll, label in (("ap", "AP"), ("coaches", "Coaches")):
            pairs = {}
            for phase in ("preseason", "final"):
                snapshot = item["snapshots"][f"{poll}_{phase}"]
                ranks = [entry["rank"] for entry in snapshot]
                ids = [str(entry["team_id"]) for entry in snapshot]
                if not valid_top25(ranks, ids):
                    raise ValueError(f"{year} {poll} {phase}: invalid top 25")
                pairs[phase] = {team_id: rank for team_id, rank in zip(ids, ranks)}
            # Research cohorts may be subsets. National publication must resolve
            # every ranked identity, including entries that appear only in final polls.
            if require_ranked_ids_mapped:
                unknown = (set(pairs['preseason']) | set(pairs['final'])) - set(team_ids)
                if unknown:
                    raise ValueError(f'{year} {label}: unmapped ranked team IDs: {sorted(unknown, key=int)}')
            # Source rankings outside the reviewed cohort are not errors.
            for team_id in sorted(team_ids):
                output.append({
                    "team": team_ids[team_id], "season": year, "poll": label,
                    "preseason_rank": pairs["preseason"].get(team_id),
                    "final_rank": pairs["final"].get(team_id),
                    "source": source, "source_sha256": item["source_sha256"],
                })
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--team-ids", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start-season", type=int, default=2016)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--require-ranked-ids-mapped", action="store_true",
                        help="Fail if any ranked team ID is missing from the reviewed national mapping")
    args = parser.parse_args()
    if args.start_season > args.end_season:
        parser.error("Invalid season range")
    snapshots = []
    for year in range(args.start_season, args.end_season + 1):
        path = args.snapshots / f"poll_snapshots_{year}.json"
        snapshots.append(json.loads(path.read_text(encoding="utf-8")))
    mapping = json.loads(args.team_ids.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in mapping.items()):
        parser.error("Team mapping must be a JSON object of ID to canonical name")
    rows = build_poll_history(snapshots, mapping, args.start_season, args.end_season,
                              require_ranked_ids_mapped=args.require_ranked_ids_mapped)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2) + "
", encoding="utf-8")


if __name__ == "__main__":
    main()
