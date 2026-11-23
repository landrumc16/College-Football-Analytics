"""Postseason games: published results and predictions from the existing official formula (ratings unchanged)."""
from datetime import datetime, timezone

from cfb_analytics import postseason as ps
from cfb_analytics.model import model_home_margin, win_probability_from_rating_gap

RAW = [
    {"id": 401900001, "season": 2026, "week": 1, "seasonType": "postseason", "homeTeam": "Georgia", "awayTeam": "Miami",
     "neutralSite": True, "startDate": "2027-01-01T21:00:00.000Z", "completed": False, "homePoints": None, "awayPoints": None,
     "notes": "Rose Bowl - CFP Quarterfinal"},
    {"id": 401900002, "season": 2026, "week": 1, "seasonType": "postseason", "homeTeam": "Texas Tech", "awayTeam": "Utah",
     "neutralSite": False, "startDate": "2026-12-20T01:00:00.000Z", "completed": True, "homePoints": 31, "awayPoints": 24,
     "notes": "CFP First Round"},
]
REPORT = {"retrieved_at": "2026-12-08T00:00:00Z", "model_metadata": {"model_id": "workbook_2026_baseline", "home_field_advantage": 3.0, "prediction_scale": 18.0},
          "rankings": [{"team": "Georgia", "rating": 24.0}, {"team": "Miami (FL)", "rating": 21.5}, {"team": "Texas Tech", "rating": 18.0}, {"team": "Utah", "rating": 19.0}]}


def test_snapshot_normalises_names_labels_and_status():
    snap = ps.snapshot(RAW, 2026, "2026-12-20T03:00:00+00:00")
    by = {g["game_id"]: g for g in snap["games"]}
    assert by[401900001]["away"] == "Miami (FL)" and by[401900001]["label"] == "Rose Bowl - CFP Quarterfinal"
    assert by[401900002]["completed"] and (by[401900002]["home_score"], by[401900002]["away_score"]) == (31, 24)
    assert [g["game_id"] for g in snap["games"]] == [401900002, 401900001]          # chronological


def test_predictions_use_the_official_formula_and_published_ratings_only():
    pub = ps.public(ps.snapshot(RAW, 2026, "t"), REPORT)
    by = {g["game_id"]: g for g in pub["games"]}
    pred = by[401900001]["prediction"]
    margin = model_home_margin(24.0, 21.5, neutral=True)                              # neutral: no home edge
    assert pred["home_margin"] == round(margin, 2) and pred["predicted_winner"] == "Georgia"
    assert pred["home_win_probability"] == round(win_probability_from_rating_gap(margin, 18.0), 4)
    assert "prediction" not in by[401900002]                                          # completed games show results only
    assert pub["model_id"] == "workbook_2026_baseline"


def test_quota_gate_skips_the_call_until_postseason_games_can_exist():
    assert not ps.should_fetch(datetime(2026, 11, 22, tzinfo=timezone.utc), {})
    assert ps.should_fetch(datetime(2026, 12, 2, tzinfo=timezone.utc), {})
    assert ps.should_fetch(datetime(2027, 1, 5, tzinfo=timezone.utc), {})
    assert ps.should_fetch(datetime(2026, 11, 22, tzinfo=timezone.utc), {"games": [{"game_id": 1}]})
