"""Generate the shared V4 descriptive team/comparison payload from sourced JSON.

Usage:
  python -m cfb_analytics.v4_program_intelligence_cli \
    --strength-input season_strength.json --poll-input poll_history.json \
    --latest-completed-season 2025 --output web/public/v4-program-intelligence.json

Input files must contain JSON arrays. Strength records require team, season,
strength (comparable opponent-adjusted units), source. Poll records require
team, season, poll (AP/Coaches), preseason_rank, final_rank, source.
The script never downloads or manufactures source data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .v4_program_intelligence import build_program_intelligence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strength-input", type=Path, required=True)
    parser.add_argument("--poll-input", type=Path, required=True)
    parser.add_argument("--latest-completed-season", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    strength = json.loads(args.strength_input.read_text(encoding="utf-8"))
    polls = json.loads(args.poll_input.read_text(encoding="utf-8"))
    if not isinstance(strength, list) or not isinstance(polls, list):
        parser.error("Input files must each contain a JSON array")
    report = build_program_intelligence(strength, polls, args.latest_completed_season)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
