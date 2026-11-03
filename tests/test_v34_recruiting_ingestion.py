import pytest
from cfb_analytics.v34_recruiting_ingestion import normalize_recruiting_classes


def test_recruiting_class_provenance_not_mistaken_for_pregame_publication():
    rows = normalize_recruiting_classes([{"year": 2024, "team": "Georgia",
                                          "points": 320.5, "rank": 1}],
                                        retrieved_at="2026-11-03T12:00:00Z")
    assert rows[0]["recruiting_points"] == 320.5
    assert rows[0]["historical_asof_verified"] is False
    assert "published_at" not in rows[0]


def test_recruiting_class_duplicate_and_invalid_values_rejected():
    row = {"year": 2024, "team": "Georgia", "points": 300.0, "rank": 1}
    with pytest.raises(ValueError, match="Duplicate"):
        normalize_recruiting_classes([row, row], retrieved_at="2026-11-03T12:00:00Z")
    with pytest.raises(ValueError):
        normalize_recruiting_classes([{**row, "points": float("nan")}],
                                    retrieved_at="2026-11-03T12:00:00Z")
