"""Production model provenance contract."""
import pytest
from cfb_analytics.pipeline import build_season_report


def test_model_metadata_is_explicit_and_incumbent():
    # Exercise metadata on a small complete roster with no completed games.
    # Use enough teams for the five-champion/seven-at-large bracket.
    roster = [{"name": f"School {i}", "conference": f"League {i // 4}", "prior": float(i)}
              for i in range(24)]
    snapshot = {"season": 2026, "source": "test-fixture",
                "retrieved_at": "2026-09-01T00:00:00Z", "games": []}
    report = build_season_report(snapshot, roster)
    metadata = report["model_metadata"]
    assert metadata["model_id"] == "workbook_2026_baseline"
    assert metadata["model_status"] == "incumbent_not_v3_promoted"
    assert metadata["prediction_scale"] == 18.0
    assert metadata["home_field_advantage"] == 3.0


def test_cfp_rejects_insufficient_conference_champions():
    roster = [{"name": f"School {i}", "conference": "Only League", "prior": float(i)}
              for i in range(24)]
    snapshot = {"season": 2026, "source": "test-fixture",
                "retrieved_at": "2026-09-01T00:00:00Z", "games": []}
    with pytest.raises(ValueError, match="at least five eligible conference champions"):
        build_season_report(snapshot, roster)
