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
    assert saved["data_changed_at"] == saved["retrieved_at"]
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
        before = json.loads(output.read_text())
        refresh(2026, output, "test-key")
    after = json.loads(output.read_text())
    assert after["games"] == before["games"]
    assert after["data_changed_at"] == before["data_changed_at"]
    assert after["retrieved_at"] >= before["retrieved_at"]


def test_changed_score_updates_snapshot(tmp_path):
    output = tmp_path / "snapshot.json"
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[sample_game()]):
        refresh(2026, output, "test-key")
    with patch("cfb_analytics.refresh.fetch_cfbd_games",
               return_value=[{**sample_game(), "home_points": 35}]):
        refresh(2026, output, "test-key")
    changed = json.loads(output.read_text())
    assert changed["games"][0]["home_score"] == 35
    assert changed["data_changed_at"] == changed["retrieved_at"]


def test_legacy_snapshot_preserves_original_change_time(tmp_path):
    output = tmp_path / "snapshot.json"
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[sample_game()]):
        refresh(2026, output, "test-key")
        legacy = json.loads(output.read_text())
        original_time = legacy.pop("data_changed_at")
        output.write_text(json.dumps(legacy))
        refresh(2026, output, "test-key")
    updated = json.loads(output.read_text())
    assert updated["data_changed_at"] == original_time
    assert updated["games"] == legacy["games"]


def test_refresh_skips_future_games_with_unknown_opponents(tmp_path):
    output = tmp_path / "snapshot.json"
    tbd = {**sample_game(), "id": 101, "home_team": None,
           "away_team": "B", "home_points": None, "away_points": None}
    with patch("cfb_analytics.refresh.fetch_cfbd_games",
               return_value=[sample_game(), tbd]):
        summary = refresh(2026, output, "test-key")
    assert summary == {"scheduled": 1, "completed": 1, "pending": 0}
    assert [g["game_id"] for g in json.loads(output.read_text())["games"]] == [100]


def test_refresh_still_rejects_same_team_on_both_sides(tmp_path):
    output = tmp_path / "snapshot.json"
    bad = {**sample_game(), "away_team": "A"}
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[bad]):
        with pytest.raises(ValueError, match="Invalid participants"):
            refresh(2026, output, "test-key")
    assert not output.exists()


def test_refresh_accepts_actual_cfbd_camelcase_fields(tmp_path):
    output = tmp_path / "snapshot.json"
    row = {"id": 401906048, "season": 2026, "week": 8,
           "homeTeam": "A", "awayTeam": "B", "homePoints": 21,
           "awayPoints": 14, "neutralSite": True, "completed": True}
    with patch("cfb_analytics.refresh.fetch_cfbd_games", return_value=[row]):
        result = refresh(2026, output, "test-key")
    assert result == {"scheduled": 1, "completed": 1, "pending": 0}
    saved = json.loads(output.read_text())["games"][0]
    assert (saved["home"], saved["away"]) == ("A", "B")
    assert (saved["home_score"], saved["away_score"]) == (21, 14)
    assert saved["neutral_site"] is True
