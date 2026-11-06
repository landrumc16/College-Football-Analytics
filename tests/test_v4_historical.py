import pytest

from cfb_analytics.v4_historical import validate_historical_rows


def game(**updates):
    row = dict(season=2023, game_id="2023-a-b", week=2,
               kickoff_at="2023-09-09T18:00:00Z",
               home="A", away="B", home_score=21, away_score=14,
               source="dated-source-1", source_as_of="2023-09-08T16:00:00Z",
               prediction_kind="retrospective")
    row.update(updates)
    return row


def test_historical_as_of_validation_and_no_automatic_release():
    report = validate_historical_rows([game()])
    assert report["seasons"] == [2023]
    assert report["prediction_kinds"]["retrospective"] == 1
    assert not report["eligible_for_release"]


def test_reject_future_source_and_missing_timezone():
    with pytest.raises(ValueError, match="not available before kickoff"):
        validate_historical_rows([game(source_as_of="2023-09-10T00:00:00Z")])
    with pytest.raises(ValueError, match="UTC offset"):
        validate_historical_rows([game(kickoff_at="2023-09-09T18:00:00")])


def test_reject_unarchived_or_late_prospective_forecast():
    with pytest.raises(ValueError, match="archive provenance"):
        validate_historical_rows([game(prediction_kind="prospective")])
    with pytest.raises(ValueError, match="not archived before kickoff"):
        validate_historical_rows([game(prediction_kind="prospective", archive_id="a1",
                                       predicted_at="2023-09-10T01:00:00Z")])


def test_reject_duplicate_games_and_accept_genuine_archive_metadata():
    with pytest.raises(ValueError, match="Duplicate"):
        validate_historical_rows([game(), game()])
    report = validate_historical_rows([game(prediction_kind="prospective", archive_id="a1",
                                            predicted_at="2023-09-09T12:00:00Z")])
    assert report["prediction_kinds"]["prospective"] == 1
