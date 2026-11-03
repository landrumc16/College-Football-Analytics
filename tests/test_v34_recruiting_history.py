import json
import pytest
from cfb_analytics import v34_recruiting_history as history


def test_multiseason_fetch_and_counts(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "fetch_classes", lambda y, key: [
        {"year": y, "team": "Georgia", "points": 300.0, "rank": 1}])
    path = tmp_path / "history.json"
    counts = history.refresh_history([2023, 2022], path, "test")
    data = json.loads(path.read_text())
    assert counts == {"2022": 1, "2023": 1}
    assert [r["season"] for r in data["classes"]] == [2022, 2023]
    assert data["historical_asof_verified"] is False


def test_partial_fetch_failure_keeps_previous_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "history.json"
    path.write_text('{"previous": true}')
    monkeypatch.setattr(history, "fetch_classes", lambda y, key: [] if y == 2023 else [
        {"year": y, "team": "Georgia", "points": 300.0}])
    with pytest.raises(ValueError, match="Empty"):
        history.refresh_history([2022, 2023], path, "test")
    assert json.loads(path.read_text()) == {"previous": True}
