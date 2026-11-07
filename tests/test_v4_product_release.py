"""Ensure the descriptive V4 release cannot quietly swap forecasting engines."""
import json
from pathlib import Path

import pytest

from scripts.verify_v4_product_release import validate_product_report


def report():
    return {
        "model_metadata": {
            "model_id": "workbook_2026_baseline",
            "model_status": "incumbent_not_v3_promoted",
            "historical_study": "retrospective_research_only",
        },
        "predictions": [{"game_id": 1, "home": "A", "away": "B",
                         "predicted_winner": "A", "home_win_probability": .7}],
    }


def test_existing_incumbent_is_allowed():
    assert validate_product_report(report())["challenger_promoted"] is False


@pytest.mark.parametrize("key,value", [
    ("model_id", "v4_challenger"),
    ("model_status", "promoted"),
    ("historical_study", "prospective_verified"),
])
def test_challenger_or_misleading_metadata_rejected(key, value):
    candidate = report()
    candidate["model_metadata"][key] = value
    with pytest.raises(ValueError):
        validate_product_report(candidate)


def test_invalid_prediction_rejected():
    candidate = report()
    candidate["predictions"][0]["home_win_probability"] = 1.2
    with pytest.raises(ValueError):
        validate_product_report(candidate)


def test_committed_product_data_uses_incumbent():
    path = Path(__file__).resolve().parents[1] / "data" / "season-2026-report.json"
    assert validate_product_report(json.loads(path.read_text()))["predictions"] > 0
