"""Acquire NCAA-origin historical schedule releases for independent review.

This downloads the published *NCAA-origin* schedule files (not ESPN mirrors).
It records hashes and source URLs and inspects columns before any FBS-only
reconciliation. It never changes the production historical archive.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

BASE = ("https://github.com/sportsdataverse/sportsdataverse-data/"
        "releases/download/ncaa_mfb_schedule/")
SOURCE = "https://github.com/sportsdataverse/ncaa-mfb-football-data"


def acquire(output_dir: Path, *, first: int = 2016, last: int = 2025) -> dict:
    if first < 2013 or last > 2025 or first > last:
        raise ValueError("Requested years must fall within completed 2013-2025 seasons")
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = {"status": "raw_ncaa_origin_not_yet_reconciled",
                 "upstream": "https://stats.ncaa.org/",
                 "producer": SOURCE, "seasons": []}
    for year in range(first, last + 1):
        filename = f"ncaa_mfb_schedule_{year}.csv.gz"
        url = BASE + filename
        with urlopen(url, timeout=90) as response:
            compressed = response.read()
        rows = list(csv.DictReader(gzip.decompress(compressed).decode("utf-8-sig").splitlines()))
        if not rows:
            raise ValueError(f"No NCAA schedule rows for {year}")
        columns = list(rows[0])
        target = output_dir / filename
        target.write_bytes(compressed)
        inventory["seasons"].append({
            "season": year, "url": url, "sha256": hashlib.sha256(compressed).hexdigest(),
            "row_count": len(rows), "columns": columns,
            "first_row": rows[0], "path": filename,
        })
    (output_dir / "inventory.json").write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return inventory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--first", type=int, default=2016)
    parser.add_argument("--last", type=int, default=2025)
    args = parser.parse_args()
    inventory = acquire(args.output_dir, first=args.first, last=args.last)
    for item in inventory["seasons"]:
        print(f"{item['season']}: {item['row_count']} rows; columns: {', '.join(item['columns'])}")
    print("Raw NCAA-origin evidence only; not approved for publication.")


if __name__ == "__main__":
    main()
