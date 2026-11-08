"""Summarize historical source coverage without publishing unverified program ranks."""
from __future__ import annotations

import json
from pathlib import Path


def build_coverage_summary(coverage: dict, walkforward: dict) -> dict:
    seasons = coverage["seasons"]
    if not isinstance(seasons, dict) or not seasons:
        raise ValueError("Historical coverage must contain seasons")
    if walkforward.get("type") != "retrospective_walk_forward_baseline":
        raise ValueError("Unexpected historical diagnostic type")
    by_season = {}
    for year in sorted(seasons):
        source = seasons[year]
        diagnostic = walkforward["by_season"].get(year)
        if diagnostic is None:
            raise ValueError(f"Missing diagnostic season {year}")
        if not isinstance(source.get("source_sha256"), str) or len(source["source_sha256"]) != 64:
            raise ValueError(f"Invalid source checksum: {year}")
        if not isinstance(source.get("extracted_sha256"), str) or len(source["extracted_sha256"]) != 64:
            raise ValueError(f"Invalid extract checksum: {year}")
        if source["completed_fbs_vs_fbs"] != diagnostic["games"]:
            raise ValueError(f"Historical game count mismatch: {year}")
        by_season[year] = {
            "source_url": source["source_url"],
            "source_sha256": source["source_sha256"],
            "extracted_sha256": source["extracted_sha256"],
            "fbs_vs_fbs_games": source["completed_fbs_vs_fbs"],
            "fbs_vs_other_games": source["completed_fbs_vs_other"],
            "disrupted_season": int(year) == 2020,
            "retrospective_elo_brier": diagnostic["brier"],
            "retrospective_elo_logloss": diagnostic["logloss"],
        }
    return {
        "status": "historical_source_coverage_only",
        "season_count": len(by_season),
        "seasons": by_season,
        "predictive_promotion_eligible": False,
        "program_rankings_publishable": False,
        "limitations": [
            "Historical final scores do not establish availability of pregame features",
            "Retrospective Elo is not the frozen production workbook baseline",
            "Historical AP/Coaches poll, roster and coaching provenance remain separate requirements",
            "2020 is a disrupted season; do not interpret it as an ordinary full schedule",
        ],
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    coverage = json.loads((args.input / "coverage.json").read_text())
    walkforward = json.loads((args.input / "walkforward_report.json").read_text())
    report = build_coverage_summary(coverage, walkforward)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
