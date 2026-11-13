"""Offline integrity gate for retained V5 historical schedule evidence.

This checks provenance manifests and bytes, not the independent correctness
of the upstream sports results. No data is promoted by this utility.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile


def verify_archive(archive: Path) -> dict:
    failures = []
    checked = []
    with ZipFile(archive) as z:
        members = set(z.namelist())
        if "coverage.json" not in members:
            raise ValueError("Missing coverage.json manifest")
        manifest = json.loads(z.read("coverage.json"))
        seasons = manifest.get("seasons")
        if not isinstance(seasons, dict) or not seasons:
            raise ValueError("Missing season coverage records")
        for season, metadata in sorted(seasons.items()):
            if not isinstance(metadata, dict) or not (season.isdigit() and len(season) == 4):
                failures.append(f"Invalid season metadata: {season}")
                continue
            paths = ((f"cfb_schedules_{season}.parquet", "source_sha256"),
                     (f"games_{season}.json", "extracted_sha256"))
            for name, digest_key in paths:
                expected = metadata.get(digest_key)
                if not isinstance(expected, str) or len(expected) != 64:
                    failures.append(f"{season}: missing {digest_key}")
                elif name not in members:
                    failures.append(f"{season}: missing {name}")
                else:
                    actual = hashlib.sha256(z.read(name)).hexdigest()
                    if actual != expected:
                        failures.append(f"{season}: checksum mismatch {name}")
            source_path = f"cfb_schedules_{season}.parquet"
            if source_path in members and len(z.read(source_path)) != metadata.get("source_bytes"):
                failures.append(f"{season}: source byte count mismatch")
            game_path = f"games_{season}.json"
            if game_path in members:
                games = json.loads(z.read(game_path))
                if not isinstance(games, list) or len(games) != metadata.get("extracted_games"):
                    failures.append(f"{season}: extracted game count mismatch")
                else:
                    identifiers = [row.get("game_id") for row in games if isinstance(row, dict)]
                    if len(identifiers) != len(games) or any(not str(game_id).strip() or game_id is None for game_id in identifiers) or len(set(identifiers)) != len(identifiers):
                        failures.append(f"{season}: missing or duplicate game identifiers")
                    if any(not isinstance(row, dict) or row.get("season") != int(season) for row in games):
                        failures.append(f"{season}: conflicting season labels")
                    fbs = sum(row.get("fbs_game") is True for row in games)
                    if fbs != metadata.get("completed_fbs_vs_fbs"):
                        failures.append(f"{season}: FBS game count mismatch")
                    if len(games) - fbs != metadata.get("completed_fbs_vs_other"):
                        failures.append(f"{season}: FBS-vs-other count mismatch")
                    checked.append({"season": int(season), "games": len(games)})
    return {"status": "pass" if not failures else "fail", "seasons_checked": len(checked),
            "games_checked": sum(item["games"] for item in checked),
            "failures": failures, "scope": "integrity_only_not_independent_source_verification"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    result = verify_archive(args.archive)
    print(json.dumps(result, indent=2))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
