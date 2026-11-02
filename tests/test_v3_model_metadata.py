"""Production model provenance contract."""
from cfb_analytics.pipeline import build_season_report


def test_model_metadata_is_explicit_and_incumbent():
    # Exercise metadata on a small complete roster with no completed games.
    # Existing pipeline needs 12+ teams for CFP simulation.
    roster = [{"name": f"School {i}", "conference": "League", "prior": float(i)}
              for i in range(12)]
    snapshot = {"season": 2026, "source": "test-fixture",
                "retrieved_at": "2026-09-01T00:00:00Z", "games": []}
    report = build_season_report(snapshot, roster)
    metadata = report["model_metadata"]
    assert metadata["model_id"] == "workbook_2026_baseline"
    assert metadata["model_status"] == "incumbent_not_v3_promoted"
    assert metadata["prediction_scale"] == 18.0
    assert metadata["home_field_advantage"] == 3.0
