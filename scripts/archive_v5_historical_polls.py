"""Create reproducible, research-only historical poll archive from source releases.

Never promote source snapshots to independently verified rankings automatically.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.fetch_v5_historical_polls import BASE, extract_snapshots, fetch_source


def archive(destination: Path, start: int = 2016, end: int = 2024) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for year in range(start, end + 1):
        raw = fetch_source(BASE.format(year=year))
        snapshot = extract_snapshots(raw, year)
        name = f"poll-snapshots-{year}.json"
        (destination / name).write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        records.append({"season": year, "path": name,
                        "source_url": snapshot["source_url"],
                        "source_sha256": snapshot["source_sha256"],
                        "source_weeks": snapshot["source_weeks"],
                        "status": "source_extracted_requires_independent_review"})
    manifest = {
        "status": "research_only_not_independently_verified",
        "publishable": False,
        "source_review_attested": False,
        "seasons": records,
        "excluded_seasons": [2025],
        "exclusion_reason": "2025 source week-2 rankings were incorrectly labeled preseason; authentic August polls require separate ingestion",
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research/archive/polls"))
    args = parser.parse_args()
    result = archive(args.output)
    print(f"Archived {len(result['seasons'])} seasons, research-only; 2025 excluded")


if __name__ == "__main__":
    main()
