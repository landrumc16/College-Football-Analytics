"""Resolve poll ESPN IDs against ESPN's published college-football team directory.

Output is an *unreviewed candidate* identity mapping, never a source-review
attestation. Human/independent source review remains required for publication.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import urlopen

DIRECTORY_URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams?limit=500"


def directory_id_names(payload: dict) -> dict[str, str]:
    """Extract explicit ESPN ID/name pairs; reject conflicting identities."""
    mapping: dict[str, str] = {}
    for league in payload.get("sports", []):
        for group in league.get("leagues", []):
            for entry in group.get("teams", []):
                team = entry.get("team", entry)
                key, name = str(team.get("id", "")).strip(), team.get("displayName")
                if not key.isdecimal() or not isinstance(name, str) or not name.strip():
                    continue
                if key in mapping and mapping[key] != name.strip():
                    raise ValueError(f"Conflicting ESPN identity for {key}")
                mapping[key] = name.strip()
    return mapping


def candidate_mapping(snapshots: list[dict], directory: dict,
                      reviewed_cohort: dict[str, str],
                      canonical_teams: set[str] | None = None) -> dict:
    names = directory_id_names(directory)
    ids = {
        str(row["team_id"])
        for snapshot in snapshots
        for entries in snapshot["snapshots"].values()
        for row in entries
    }
    candidates = {key: names[key] for key in sorted(ids, key=int) if key in names}
    if canonical_teams is not None:
        # A display name is not necessarily the app's canonical team name.
        # Accept only unambiguous exact names or exact school locations.
        matched: dict[str, str] = {}
        for league in directory.get("sports", []):
            for group in league.get("leagues", []):
                for entry in group.get("teams", []):
                    team = entry.get("team", entry)
                    key = str(team.get("id", ""))
                    options = {team.get("location"), team.get("shortDisplayName"),
                               team.get("displayName")}
                    hits = canonical_teams.intersection(x for x in options if isinstance(x, str))
                    if key in ids and len(hits) == 1:
                        matched[key] = next(iter(hits))
        candidates = matched
    # Existing canonical names take precedence; directory display names are
    # candidates only, since program names can differ from app canonical names.
    candidates.update({key: value for key, value in reviewed_cohort.items() if key in ids})
    unresolved = sorted(ids - candidates.keys(), key=int)
    collisions: dict[str, list[str]] = {}
    for key, name in candidates.items():
        collisions.setdefault(name, []).append(key)
    return {
        "status": "candidate_only_requires_independent_identity_review",
        "publishable": False,
        "directory_source": DIRECTORY_URL,
        "ranked_ids": len(ids),
        "resolved_candidates": len(candidates),
        "unresolved_ids": unresolved,
        "duplicate_canonical_names": {
            name: keys for name, keys in collisions.items() if len(keys) > 1
        },
        "mapping": dict(sorted(candidates.items(), key=lambda item: int(item[0]))),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--poll-snapshots", type=Path, required=True)
    p.add_argument("--reviewed-cohort", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--team-season-records", type=Path, required=True)
    p.add_argument("--start-season", type=int, default=2016)
    p.add_argument("--end-season", type=int, default=2025)
    args = p.parse_args()
    if args.start_season > args.end_season:
        p.error("Invalid season range")
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    snapshots = [
        load(args.poll_snapshots / f"poll_snapshots_{year}.json")
        for year in range(args.start_season, args.end_season + 1)
    ]
    with urlopen(DIRECTORY_URL, timeout=30) as response:
        directory = json.load(response)
    records = load(args.team_season_records)
    canonical = {row["team"] for season in records["seasons"] for row in season["teams"]}
    result = candidate_mapping(snapshots, directory, load(args.reviewed_cohort),
                               canonical_teams=canonical)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + chr(10), encoding="utf-8")


if __name__ == "__main__":
    main()
