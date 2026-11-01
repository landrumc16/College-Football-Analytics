"""End-to-end frozen fixture demo smoke test."""
import json

from cfb_analytics.demo import main


def test_demo_generates_complete_dashboard_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main()
    path = tmp_path / "web" / "public" / "season-report.json"
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["season"] == 2026
    assert "NOT LIVE" in report["source"]
    assert report["summary"]["teams"] == 138
    assert report["summary"]["completed_games"] == 510
    assert report["summary"]["upcoming_games"] == 378
    assert len(report["rankings"]) == 138
    assert len(report["predictions"]) == 378
    assert {r["rank"] for r in report["rankings"]} == set(range(1, 139))
