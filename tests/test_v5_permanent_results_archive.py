"""Offline integrity checks for retained 2016-2025 team-season records."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "research" / "archive" / "results"


def test_historical_team_season_archive_integrity():
    manifest = json.loads((ROOT / "manifest.json").read_text())
    raw = (ROOT / manifest["canonical_path"]).read_bytes()
    records = json.loads(raw)
    assert hashlib.sha256(raw).hexdigest() == manifest["sha256"]
    assert manifest["publishable"] is False
    assert manifest["source_review_attested"] is False
    assert [row["season"] for row in records["seasons"]] == list(range(2016, 2026))
    assert manifest["seasons"] == list(range(2016, 2026))
    for season in records["seasons"]:
        teams = season["teams"]
        assert len(teams) >= 120
        assert len({row["team"] for row in teams}) == len(teams)
        for row in teams:
            assert row["team"].strip()
            for key in ("fbs_wins", "fbs_losses", "wins", "losses"):
                assert type(row[key]) is int and row[key] >= 0
            assert row["wins"] >= row["fbs_wins"]
            assert row["losses"] >= row["fbs_losses"]


def test_trajectory_inputs_exclude_disrupted_2020_season():
    records = json.loads((ROOT / "team-season-records-2016-2025.json").read_text())
    expected = set(range(2016, 2026)) - {2020}
    assert expected <= {row["season"] for row in records["seasons"]}


def test_published_preview_matches_permanent_source_records():
    """Catch stale or divergent displayed 3/5/10-year values without claiming source attestation."""
    source = json.loads((ROOT / "team-season-records-2016-2025.json").read_text())
    preview_path = ROOT.parents[2] / "web" / "public" / "v5-historical-results-preview.json"
    preview = json.loads(preview_path.read_text())
    assert preview["source_review_attested"] is False
    assert preview["national_grades_available"] is False
    by_year = {s["season"]: {t["team"]: t for t in s["teams"]} for s in source["seasons"]}
    for program in preview["programs"]:
        for span, window in program["windows"].items():
            expected_years = [y for y in range(2026-int(span), 2026) if y != 2020]
            assert window["seasons"] == expected_years
            rows = [by_year[y][program["team"]] for y in expected_years]
            wins = sum(row["fbs_wins"] for row in rows)
            losses = sum(row["fbs_losses"] for row in rows)
            assert (window["wins"], window["losses"]) == (wins, losses)
            assert abs(window["win_pct"] - round(wins/(wins+losses), 4)) < 0.000001
