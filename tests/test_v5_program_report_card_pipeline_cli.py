"""V5 partial publication integration regression."""
import json
import sys
import pytest
from cfb_analytics.v5_program_report_card_pipeline_cli import main

def test_reviewed_strength_can_publish_without_unreviewed_history(tmp_path, monkeypatch):
    peers = [f"Team {i}" for i in range(120)]
    source = "https://example.org/source"
    data = {
        "polls": [],
        "records": {"seasons": [{"season": year, "teams": [
            {"team": team, "fbs_wins": 6, "fbs_losses": 4} for team in peers
        ]} for year in range(2016, 2026)]},
        "rankings": [{"team": team, "rating": i} for i, team in enumerate(peers)],
        "peers": peers,
        "review": {"poll_reviewed": False, "results_reviewed": False,
                   "strength_reviewed": True, "strength_source": source,
                   "results_source": source, "eligible_fbs_source": source,
                   "eligible_fbs_reviewed": True},
    }
    for name, value in data.items():
        (tmp_path / (name + ".json")).write_text(json.dumps(value))
    output = tmp_path / "output.json"
    monkeypatch.setattr(sys, "argv", ["v5-report-cards",
        "--poll-history", str(tmp_path / "polls.json"),
        "--team-season-records", str(tmp_path / "records.json"),
        "--current-v4-rankings", str(tmp_path / "rankings.json"),
        "--eligible-fbs", str(tmp_path / "peers.json"),
        "--source-review", str(tmp_path / "review.json"),
        "--as-of", "2026-11-13", "--latest-completed-season", "2025",
        "--output", str(output)])
    main()
    result = json.loads(output.read_text())
    assert result["publication_status"] == "partial_verified_categories_only"
    assert result["sources"] == [source]
    assert result["coverage"]["strength"]["national_grades_available"]
    assert not result["coverage"]["hype"]["national_grades_available"]
    assert not result["coverage"]["trajectory"]["national_grades_available"]
    assert all(row["categories"]["strength"]["grade"] for row in result["programs"])
    assert all(row["overall_grade"] is None for row in result["programs"])
    data["review"]["strength_reviewed"] = False
    (tmp_path / "review.json").write_text(json.dumps(data["review"]))
    with pytest.raises(SystemExit):
        main()
