"""End-to-end parity gate against the frozen 138-team, 510-game baseline."""
import pytest
from cfb_analytics.parity import compare


def test_all_eight_rating_passes_and_derived_metrics():
    differences = compare()
    failures = [d for d in differences if d[0] > 1e-6]
    assert not failures, f"Workbook discrepancies: {failures[:20]}"
