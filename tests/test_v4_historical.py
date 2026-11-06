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


def test_four_season_contract_requires_real_rows_for_every_fold():
    from cfb_analytics.v4_historical import validate_held_out_cohorts
    seasons = [2021, 2022, 2023, 2024]
    with pytest.raises(ValueError, match="all and only"):
        validate_held_out_cohorts([game()], seasons)
    rows = [game(season=s, game_id=f"{s}-a-b",
                 kickoff_at=f"{s}-09-09T18:00:00Z",
                 source_as_of=f"{s}-09-08T16:00:00Z") for s in seasons]
    report = validate_held_out_cohorts(rows, seasons)
    assert report["games"] == 4
    assert all(n == 1 for n in report["games_by_season"].values())
    assert not report["promotion_eligible"]
    with pytest.raises(ValueError, match="Exactly four"):
        validate_held_out_cohorts(rows, [2021, 2022, 2023, 2023])
