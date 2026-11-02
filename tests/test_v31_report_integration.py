"""Integration regression: refresh -> pregame archive -> completed-game evaluation.

The real report entrypoint is exercised with a stubbed deterministic rating engine,
so provenance, atomic JSON persistence, and rerun behavior are tested together.
"""
import json
import sys
from datetime import datetime, timedelta, timezone

import pytest
from cfb_analytics import report as report_module


def test_report_archive_survives_refresh_and_scores_completed_game(tmp_path, monkeypatch):
    now = datetime.now(timezone.utc)
    kickoff = (now + timedelta(days=2)).isoformat()
    retrieved = now.isoformat()
    snapshot_path = tmp_path / "cfbd-2026-games.json"
    output = tmp_path / "season-2026-report.json"
    roster = [{"name": "A"}] * 69 + [{"name": "B"}] * 69
    game = {"game_id": 7, "home": "A", "away": "B", "completed": False,
            "home_score": None, "away_score": None, "start_date": kickoff}
    snapshot = {"retrieved_at": retrieved, "data_changed_at": retrieved,
                "games": [game]}
    snapshot_path.write_text(json.dumps(snapshot))
    monkeypatch.setattr(report_module, "load_baseline", lambda: (roster, None))

    def fake_run_snapshot(snapshot_file, roster_file, staging_file):
        data = json.loads(snapshot_file.read_text())
        prediction = {"game_id": 7, "home": "A", "away": "B",
                      "home_win_probability": 0.8, "home_margin": 7}
        result = {"retrieved_at": data["retrieved_at"],
                  "model_metadata": {"model_id": "workbook_2026_baseline"},
                  "predictions": [] if data["games"][0]["completed"] else [prediction],
                  "summary": {"teams": 138}}
        staging_file.write_text(json.dumps(result))
        return result

    monkeypatch.setattr(report_module, "run_snapshot", fake_run_snapshot)
    monkeypatch.setattr(sys, "argv", ["report", "--season", "2026",
                                     "--snapshot", str(snapshot_path),
                                     "--output", str(output)])
    report_module.main()
    history_path = tmp_path / "pregame-2026-history.json"
    first = json.loads(history_path.read_text())
    assert first["7"]["home_win_probability"] == 0.8
    assert first["7"]["model_id"] == "workbook_2026_baseline"
    assert json.loads(output.read_text())["prediction_accuracy"]["games_evaluated"] == 0

    # A second pregame publication must not overwrite the first valid forecast.
    def revised_run(snapshot_file, roster_file, staging_file):
        result = fake_run_snapshot(snapshot_file, roster_file, staging_file)
        if result["predictions"]:
            result["predictions"][0]["home_win_probability"] = 0.2
        return result

    monkeypatch.setattr(report_module, "run_snapshot", revised_run)
    report_module.main()
    assert json.loads(history_path.read_text()) == first

    # Postgame refresh evaluates the original forecast without inventing a new one.
    snapshot["games"][0].update(completed=True, home_score=24, away_score=14)
    snapshot_path.write_text(json.dumps(snapshot))
    report_module.main()
    latest = json.loads(output.read_text())
    assert json.loads(history_path.read_text()) == first
    assert latest["prediction_accuracy"]["games_evaluated"] == 1
    assert latest["prediction_accuracy"]["winner_accuracy"] == 1.0
    assert latest["prediction_accuracy"]["margin_mae"] == 3.0


def test_stale_snapshot_cannot_overwrite_existing_report(tmp_path, monkeypatch):
    snapshot = tmp_path / "cfbd-2026-games.json"
    output = tmp_path / "season-2026-report.json"
    output.write_text('{"previous":"valid"}')
    snapshot.write_text(json.dumps({"retrieved_at": "2020-01-01T00:00:00Z",
                                    "games": []}))
    monkeypatch.setattr(report_module, "load_baseline", lambda: ([], None))
    monkeypatch.setattr(sys, "argv", ["report", "--season", "2026",
                                     "--snapshot", str(snapshot),
                                     "--output", str(output)])
    with pytest.raises(RuntimeError, match="older than 72 hours"):
        report_module.main()
    assert json.loads(output.read_text()) == {"previous": "valid"}
