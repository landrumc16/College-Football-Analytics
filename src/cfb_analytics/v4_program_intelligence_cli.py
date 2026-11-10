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
from .v4_program_provenance import validate_program_sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strength-input", type=Path, required=True)
    parser.add_argument("--poll-input", type=Path, required=True)
    parser.add_argument("--latest-completed-season", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewed-sources", action="store_true", help="Explicit acknowledgement that source authenticity and comparable opponent-adjusted strength were independently reviewed")
    args = parser.parse_args()
    strength = json.loads(args.strength_input.read_text(encoding="utf-8"))
    polls = json.loads(args.poll_input.read_text(encoding="utf-8"))
    if not isinstance(strength, list) or not isinstance(polls, list):
        parser.error("Input files must each contain a JSON array")
    coverage = validate_program_sources(strength, polls, args.latest_completed_season)
    if not strength or not polls:
        parser.error("Both verified strength and poll history are required for publication")
    if coverage["strength_programs_full_window"] == 0 or coverage["poll_programs_full_window"] == 0:
        parser.error("No ten-season historical coverage for strength or polls; refusing publication")
    # A complete strength cohort and a separate complete poll cohort do not
    # establish a single publishable program. Require a shared ten-season team.
    years = set(range(args.latest_completed_season - 9, args.latest_completed_season + 1))
    strength_by_team = {}
    poll_by_team = {}
    for row in strength:
        strength_by_team.setdefault(row["team"], set()).add(row["season"])
    for row in polls:
        poll_by_team.setdefault((row["team"], row["poll"]), set()).add(row["season"])
    eligible = {team for team, observed in strength_by_team.items() if years <= observed}
    if not any(team in eligible and all(years <= poll_by_team.get((team, poll), set()) for poll in ("AP", "Coaches")) for team in eligible):
        parser.error("No program has matching ten-season strength, AP, and Coaches coverage; refusing publication")
    if not args.reviewed_sources:
        parser.error("Source authenticity and comparable opponent-adjusted strength require independent review; use --reviewed-sources only after verification")
    report = build_program_intelligence(strength, polls, args.latest_completed_season)
    report["source_review_attested"] = True
    report["provenance_diagnostics"] = coverage
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
