import json
from cfb_analytics import v34_recruiting_refresh as refresh_module


def test_refresh_writes_atomic_research_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(refresh_module, "fetch_classes", lambda year, key: [
        {"year": year, "team": "Georgia", "points": 300.5, "rank": 1}])
    path = tmp_path / "classes.json"
    assert refresh_module.refresh(2026, path, "test-token") == 1
    payload = json.loads(path.read_text())
    assert payload["classes"][0]["team"] == "Georgia"
    assert payload["historical_asof_verified"] is False
    assert not path.with_suffix(".json.tmp").exists()


def test_empty_recruiting_response_does_not_overwrite_snapshot(tmp_path, monkeypatch):
    path = tmp_path / "classes.json"
    path.write_text('{"preserved": true}')
    monkeypatch.setattr(refresh_module, "fetch_classes", lambda year, key: [])
    import pytest
    with pytest.raises(ValueError, match="empty"):
        refresh_module.refresh(2026, path, "test-token")
    assert json.loads(path.read_text()) == {"preserved": True}
