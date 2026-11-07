"""Fail-closed V4 release evidence assessment.

Numerical results alone cannot authorize a release. Provenance attestations
must refer to the same exact paired cohort and frozen model sources.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .v4_evaluation import assess_release_gates


REQUIRED_ATTESTATIONS = (
    "source_authenticity_verified",
    "pregame_feature_cutoffs_verified",
    "incumbent_frozen_v342_verified",
    "challenger_frozen_verified",
    "training_holdout_independence_verified",
    "same_games_and_cutoffs_verified",
    "complete_eligible_cohort_verified",
    "no_future_data_leakage_verified",
)


def canonical_digest(rows: list[dict]) -> str:
    """Bind attestations to the exact evaluated rows, independent of row order."""
    ordered = sorted(rows, key=lambda row: (row["season"], str(row["game_id"])))
    return hashlib.sha256(json.dumps(ordered, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def assess_evidence(rows: list[dict], attestations: dict | None,
                    *, seasons: list[int], draws: int = 2000) -> dict:
    """Return a release evidence verdict, never automatically merge or deploy.

    An attestation is an external review claim, not independent verification.
    Missing attestations and mismatched cohort fingerprints always fail closed.
    """
    numerical = assess_release_gates(rows, held_out_seasons=seasons, draws=draws)
    digest = canonical_digest(rows)
    attestations = attestations or {}
    checks = {key: attestations.get(key) is True for key in REQUIRED_ATTESTATIONS}
    checks["cohort_digest_matches"] = attestations.get("cohort_sha256") == digest
    checks["reviewer_identified"] = isinstance(attestations.get("reviewer"), str) and bool(attestations["reviewer"].strip())
    checks["evidence_reference_present"] = isinstance(attestations.get("evidence_reference"), str) and bool(attestations["evidence_reference"].strip())
    ready_for_manual_release_review = numerical["numerical_gates_pass"] and all(checks.values())
    return {
        "status": "ready_for_manual_release_review" if ready_for_manual_release_review else "no_go",
        "promotion_eligible": False,
        "cohort_sha256": digest,
        "numerical_gates_pass": numerical["numerical_gates_pass"],
        "provenance_checks": checks,
        "numerical_evaluation": numerical,
        "reason": "External evidence must be independently inspected; this report cannot authorize deployment.",
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate V4 paired cohort and release evidence")
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--attestations", type=Path)
    parser.add_argument("--seasons", type=int, nargs=4, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = json.loads(args.pairs.read_text())
    attestations = json.loads(args.attestations.read_text()) if args.attestations else None
    report = assess_evidence(rows, attestations, seasons=args.seasons)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": report["status"], "numerical_gates_pass": report["numerical_gates_pass"], "output": str(args.output)}))
    return 0 if report["status"] == "ready_for_manual_release_review" else 2


if __name__ == "__main__":
    raise SystemExit(main())
