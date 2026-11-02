"""Version 3.1 forecast ledger boundary and rerun regression tests."""
from cfb_analytics.forecast_ledger import archive_pending


def sample():
    report = {
        "generated_at": "2026-11-02T12:00:00+00:00",
        "retrieved_at": "2026-11-02T11:00:00Z",
        "model_metadata": {"model_id": "workbook_2026_baseline"},
        "predictions": [{"game_id": 1, "home": "Miami (FL)", "away": "Georgia",
                         "home_win_probability": 0.6, "home_margin": 4}],
    }
    snapshot = {"games": [{"game_id": 1, "home": "Miami", "away": "Georgia",
                            "completed": False, "start_date": "2026-11-03T12:00:00Z"}]}
    return report, snapshot


def test_first_valid_pregame_forecast_is_immutable():
    report, snapshot = sample()
    first = archive_pending({}, report, snapshot)
    assert first["1"]["model_id"] == "workbook_2026_baseline"
    assert first["1"]["source"] == "generated_before_kickoff"
    report["predictions"][0]["home_win_probability"] = 0.9
    assert archive_pending(first, report, snapshot) == first
    assert first["1"]["home_win_probability"] == 0.6


def test_reject_post_kickoff_and_equal_timestamp():
    report, snapshot = sample()
    for stamp in ("2026-11-02T11:59:59Z", "2026-11-02T12:00:00Z"):
        snapshot["games"][0]["start_date"] = stamp
        assert archive_pending({}, report, snapshot) == {}


def test_reject_invalid_or_missing_provenance():
    report, snapshot = sample()
    report["generated_at"] = "2026-11-02T12:00:00"
    assert archive_pending({}, report, snapshot) == {}
    report["generated_at"] = "2026-11-02T10:00:00Z"
    assert archive_pending({}, report, snapshot) == {}
    report["generated_at"] = "2026-11-02T12:00:00Z"
    snapshot["games"][0]["start_date"] = None
    assert archive_pending({}, report, snapshot) == {}


def test_reject_completed_game_identity_change_and_bad_probability():
    report, snapshot = sample()
    snapshot["games"][0]["completed"] = True
    assert archive_pending({}, report, snapshot) == {}
    snapshot["games"][0]["completed"] = False
    report["predictions"][0]["away"] = "Florida"
    assert archive_pending({}, report, snapshot) == {}
    report["predictions"][0]["away"] = "Georgia"
    for invalid in (True, -0.1, 1.1, None):
        report["predictions"][0]["home_win_probability"] = invalid
        assert archive_pending({}, report, snapshot) == {}


def test_existing_ledger_preserved_when_source_unavailable():
    report, snapshot = sample()
    original = {"1": {"source": "previously_published_forecast"}}
    report["retrieved_at"] = None
    assert archive_pending(original, report, snapshot) == original
