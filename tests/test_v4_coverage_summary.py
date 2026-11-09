import pytest

from cfb_analytics.v4_coverage_summary import build_coverage_summary


def test_coverage_summary_retains_provenance_and_blocks_publication():
    coverage = {"seasons": {"2020": {
        "source_url": "https://example.org/source", "source_sha256": "a" * 64,
        "extracted_sha256": "b" * 64, "completed_fbs_vs_fbs": 450,
        "completed_fbs_vs_other": 70}}}
    diagnostic = {"type": "retrospective_walk_forward_baseline", "by_season": {"2020": {
        "games": 450, "brier": 0.2, "logloss": 0.6}}}
    report = build_coverage_summary(coverage, diagnostic)
    assert report["season_count"] == 1
    assert report["seasons"]["2020"]["disrupted_season"] is True
    assert report["seasons"]["2020"]["source_sha256"] == "a" * 64
    assert report["predictive_promotion_eligible"] is False
    assert report["program_rankings_publishable"] is False


def test_mismatched_diagnostic_is_rejected():
    coverage = {"seasons": {"2025": {
        "source_url": "https://example.org/source", "source_sha256": "a" * 64,
        "extracted_sha256": "b" * 64, "completed_fbs_vs_fbs": 800,
        "completed_fbs_vs_other": 60}}}
    with pytest.raises(ValueError, match="count mismatch"):
        build_coverage_summary(coverage, {"type": "retrospective_walk_forward_baseline", "by_season": {"2025": {
            "games": 799, "brier": 0.2, "logloss": 0.6}}})


def test_wrong_diagnostic_type_rejected():
    with pytest.raises(ValueError, match="diagnostic type"):
        build_coverage_summary({"seasons": {"2025": {}}}, {"type": "prospective", "by_season": {}})


def test_empty_coverage_rejected():
    with pytest.raises(ValueError, match="contain seasons"):
        build_coverage_summary({"seasons": {}}, {"type": "retrospective_walk_forward_baseline"})
