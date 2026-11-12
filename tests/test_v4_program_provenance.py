import pytest

from cfb_analytics.v4_program_provenance import validate_program_sources


def test_source_coverage_is_diagnostic_not_verified():
    rows = [dict(team="A", season=y, strength=10.0 + y - 2016, source="https://example.org/verified-data")
            for y in range(2016, 2026)]
    report = validate_program_sources(rows, [], 2025)
    assert report["strength_programs_full_window"] == 1
    assert report["historical_rankings_ready"] is False
    assert report["source_authenticity_verified"] is False


def test_rejects_unsourced_and_future_data():
    with pytest.raises(ValueError, match="source"):
        validate_program_sources([dict(team="A", season=2025, source="unknown")], [], 2025)
    with pytest.raises(ValueError, match="window"):
        validate_program_sources([dict(team="A", season=2026, source="https://example.org")], [], 2025)
    with pytest.raises(ValueError, match="source"):
        validate_program_sources([dict(team="A", season=2025, source="sha256:bad")], [], 2025)
