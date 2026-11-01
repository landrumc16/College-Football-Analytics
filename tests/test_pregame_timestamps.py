"""Regression tests for timestamp-based pregame forecast eligibility."""
from cfb_analytics.ingestion import normalize_cfbd_games
from cfb_analytics.report import verified_pregame


def test_kickoff_timestamp_survives_ingestion():
    records = [{
        "id": 101, "season": 2026, "week": 9,
        "homeTeam": "Alabama", "awayTeam": "Auburn",
        "startDate": "2026-11-01T18:00:00Z",
        "homePoints": 21, "awayPoints": 17,
    }]
    game, = normalize_cfbd_games(records, 2026)
    assert game.start_date == "2026-11-01T18:00:00Z"
    assert game.completed


def test_pregame_forecast_requires_strictly_earlier_publication():
    kickoff = "2026-11-01T18:00:00Z"
    assert verified_pregame("2026-11-01T17:59:59+00:00", kickoff)
    assert not verified_pregame(kickoff, kickoff)
    assert not verified_pregame("2026-11-01T18:00:01Z", kickoff)


def test_pregame_forecast_rejects_missing_invalid_or_naive_times():
    kickoff = "2026-11-01T18:00:00Z"
    for invalid in (None, "", "not-a-time", "2026-11-01T17:00:00"):
        assert not verified_pregame(invalid, kickoff)
        assert not verified_pregame("2026-11-01T17:00:00Z", invalid)


def test_pregame_forecast_compares_offsets_in_utc():
    assert verified_pregame("2026-11-01T12:00:00-05:00", "2026-11-01T18:00:00Z")
    assert not verified_pregame("2026-11-01T13:00:00-05:00", "2026-11-01T18:00:00Z")
