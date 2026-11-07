"""Release evidence gates must fail closed when provenance is missing or unbound."""
import pytest

from cfb_analytics.v4_release_evidence import (
    REQUIRED_ATTESTATIONS, assess_evidence, canonical_digest,
)


def paired_rows():
    rows = []
    for season in (2022, 2023, 2024, 2025):
        for week in range(1, 5):
            for game in range(3):
                rows.append({
                    "season": season, "week": week, "game_id": f"{season}-{week}-{game}",
                    "outcome": game % 2, "incumbent_probability": 0.5,
                    "challenger_probability": 0.15 if game % 2 == 0 else 0.85,
                    "prediction_kind": "retrospective",
                })
    return rows


def test_no_provenance_cannot_promote_even_when_numerical_gates_pass():
    result = assess_evidence(paired_rows(), None, seasons=[2022, 2023, 2024, 2025], draws=100)
    assert result["numerical_gates_pass"] is True
    assert result["status"] == "no_go"
    assert result["promotion_eligible"] is False
    assert not result["provenance_checks"]["cohort_digest_matches"]


def test_attestations_bind_to_exact_rows_and_require_review():
    rows = paired_rows()
    attestations = {key: True for key in REQUIRED_ATTESTATIONS}
    attestations.update(cohort_sha256=canonical_digest(rows), reviewer="Independent reviewer",
                        evidence_reference="archived-source-evidence")
    result = assess_evidence(rows, attestations, seasons=[2022, 2023, 2024, 2025], draws=100)
    assert result["status"] == "ready_for_manual_release_review"
    assert result["promotion_eligible"] is False
    rows[0]["challenger_probability"] = 0.16
    result = assess_evidence(rows, attestations, seasons=[2022, 2023, 2024, 2025], draws=100)
    assert result["status"] == "no_go"
    assert not result["provenance_checks"]["cohort_digest_matches"]


def test_invalid_cohort_rejected():
    with pytest.raises(ValueError, match="four distinct"):
        assess_evidence(paired_rows(), None, seasons=[2022, 2022, 2024, 2025], draws=100)


def test_digest_independent_of_input_order():
    rows = paired_rows()
    assert canonical_digest(rows) == canonical_digest(list(reversed(rows)))
