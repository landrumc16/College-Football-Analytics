"""Offline integrity checks for the permanent historical poll research archive."""
import json
from pathlib import Path

from scripts.fetch_v5_historical_polls import valid_top25

ROOT = Path(__file__).resolve().parents[1] / "research" / "archive" / "polls"


def test_archived_seasons_are_complete_and_reusable_without_network():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert manifest["publishable"] is False
    assert manifest["source_review_attested"] is False
    assert [item["season"] for item in manifest["seasons"]] == list(range(2016, 2025))
    assert manifest["excluded_seasons"] == [2025]
    assert {p.name for p in ROOT.glob("poll-snapshots-*.json")} == {
        f"poll-snapshots-{year}.json" for year in range(2016, 2025)
    }
    for entry in manifest["seasons"]:
        data = json.loads((ROOT / entry["path"]).read_text())
        assert data["season"] == entry["season"]
        assert data["source_url"] == entry["source_url"]
        assert data["source_sha256"] == entry["source_sha256"]
        assert data["source_weeks"] == entry["source_weeks"]
        assert set(data["snapshots"]) == {
            "ap_preseason", "ap_final", "coaches_preseason", "coaches_final"
        }
        for rows in data["snapshots"].values():
            assert valid_top25(
                [row["rank"] for row in rows],
                [row["team_id"] for row in rows],
            )


def test_archive_never_confuses_source_integrity_with_independent_review():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    assert all(
        entry["status"] == "source_extracted_requires_independent_review"
        for entry in manifest["seasons"]
    )
