"""Integration tests for refresh publishing without external API calls."""
import json
from unittest.mock import patch

import pytest

from cfb_analytics.refresh import refresh


def sample_game():
    return {"id": 100, "season": 2026, "week": 1,
            "home_team": "A", "away_team": "B",
            "home_points": 31, "away_points": 17}


def test_refresh_publishes_validated_snapshot(tmp_path):
    output = tmp_path / "snapshot.json"
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[sample_game()]):
        result = refresh(2026, output, "test-key")
    assert result == {"scheduled": 1, "completed": 1, "pending": 0}
    saved = json.loads(output.read_text())
    assert saved["games"][0]["home"] == "A"
    assert saved["games"][0]["home_score"] == 31
    assert not output.with_suffix(".json.tmp").exists()


def test_refresh_does_not_overwrite_on_invalid_response(tmp_path):
    output = tmp_path / "snapshot.json"
    output.write_text("previous-good-snapshot")
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[]):
        with pytest.raises(RuntimeError):
            refresh(2026, output, "test-key")
    assert output.read_text() == "previous-good-snapshot"


def test_refresh_deduplicates_identical_api_ids(tmp_path):
    output = tmp_path / "snapshot.json"
    row = sample_game()
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[row, row]):
        result = refresh(2026, output, "test-key")
    assert result["scheduled"] == 1
    assert len(json.loads(output.read_text())["games"]) == 1


def test_refresh_rejects_cross_season_rows(tmp_path):
    output = tmp_path / "snapshot.json"
    with patch("cfb_analytics.refresh.fetch_cfbd_games",
               return_value=[sample_game(), {**sample_game(), "id": 101, "season": 2025}]):
        with pytest.raises(RuntimeError, match="cross-season"):
            refresh(2026, output, "test-key")
    assert not output.exists()


def test_unchanged_refresh_preserves_original_snapshot(tmp_path):
    output = tmp_path / "snapshot.json"
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[sample_game()]):
        refresh(2026, output, "test-key")
        before = output.read_bytes()
        refresh(2026, output, "test-key")
    assert output.read_bytes() == before


def test_changed_score_updates_snapshot(tmp_path):
    output = tmp_path / "snapshot.json"
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[sample_game()]):
        refresh(2026, output, "test-key")
    with patch("cfb_analytics.refresh.fetch_cfbd_games",
               return_value=[{**sample_game(), "home_points": 35}]):
        refresh(2026, output, "test-key")
    assert json.loads(output.read_text())["games"][0]["home_score"] == 35
