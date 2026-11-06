from pathlib import Path

from cfb_analytics.v4_baseline_manifest import build_manifest


def test_baseline_manifest_is_reproducible_and_not_release_evidence():
    root = Path(__file__).resolve().parents[1]
    first = build_manifest(root)
    assert first == build_manifest(root)
    assert first["historical_seasons"] == [2026]
    assert first["fbs_team_count"] == 138
    assert first["completed_fixture_games"] == 510
    assert first["eligible_for_v4_multiseason_release_gate"] is False
    assert len(first["fixture_hashes"]) > 0
    assert all(len(entry["sha256"]) == 64 for entry in
               first["fixture_hashes"] + first["incumbent_source_hashes"])
