"""Acquire and validate authentic preseason/final AP and Coaches snapshots.

Research-only output. Publication requires independent source and identity review.
SportsDataverse documents regular week 1 as preseason, postseason week 1
as final, and null-ranked exit rows as non-ranked.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

BASE = ("https://github.com/sportsdataverse/sportsdataverse-data/"
        "releases/download/cfb_poll_analytics/cfb_poll_analytics_{year}.csv")


def valid_top25(ranks: list[int], ids: list[str]) -> bool:
    """Allow genuine tied poll positions (competition ranking: 1, 2, 2, 4)."""
    if len(ranks) != 25 or len(ids) != 25 or len(set(ids)) != 25 or not all(ids):
        return False
    ordered = sorted(ranks)
    return all(rank == index or (index > 1 and rank == ordered[index - 2])
               for index, rank in enumerate(ordered, start=1))


def extract_snapshots(data: bytes, year: int) -> dict:
    rows = list(csv.DictReader(data.decode("utf-8-sig").splitlines()))
    if not rows:
        raise ValueError(f"{year}: empty poll source")
    snapshots = {}
    for poll in ("ap", "coaches"):
        for phase, season_type in (("preseason", 2), ("final", 3)):
            selected = [r for r in rows if int(r["season"]) == year
                        and int(r["season_type"]) == season_type
                        and int(r["week"]) == 1 and r["poll"].lower() == poll
                        and r["rank"] not in ("", "null", "NA")]
            if len(selected) != 25:
                raise ValueError(f"{year} {poll} {phase}: expected 25 ranks, got {len(selected)}")
            ranks = [int(r["rank"]) for r in selected]
            ids = [str(r["team_id"]).strip() for r in selected]
            if not valid_top25(ranks, ids):
                raise ValueError(
                    f"{year} {poll} {phase}: duplicate or invalid ranks/team IDs; "
                    f"ranks={ranks!r}; team_ids={ids!r}"
                )
            snapshots[f"{poll}_{phase}"] = [
                {"team_id": team_id, "rank": rank}
                for rank, team_id in sorted(zip(ranks, ids))
            ]
    return {"season": year, "source_url": BASE.format(year=year),
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "snapshots": snapshots}


def fetch_source(url: str) -> bytes:
    """Retry transient source outages, but fail immediately on missing releases."""
    for attempt in range(3):
        try:
            with urlopen(url, timeout=90) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise RuntimeError(f"Poll source request failed: {url} (HTTP {exc.code})") from exc
        except URLError as exc:
            if attempt == 2:
                raise RuntimeError(f"Poll source unavailable after 3 attempts: {url}") from exc
        sleep(attempt + 1)
    raise AssertionError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=2016)
    parser.add_argument("--end-season", type=int, default=2025)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.start_season > args.end_season:
        parser.error("Invalid season range")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    for year in range(args.start_season, args.end_season + 1):
        url = BASE.format(year=year)
        raw = fetch_source(url)
        # Preserve source evidence even when a season fails validation.
        (args.output / f"poll_source_{year}.csv").write_bytes(raw)
        snapshot = extract_snapshots(raw, year)
        (args.output / f"poll_snapshots_{year}.json").write_text(
            json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
        manifest.append({"season": year, "sha256": snapshot["source_sha256"],
                         "source_url": url, "snapshot_sizes":
                         {k: len(v) for k, v in snapshot["snapshots"].items()}})
    (args.output / "poll_manifest.json").write_text(json.dumps({
        "status": "research_only_requires_independent_source_and_team_identity_review",
        "source_documentation": "https://github.com/sportsdataverse/cfbfastR-cfb-data/blob/main/DATASETS.md",
        "seasons": manifest, "publishable": False
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
