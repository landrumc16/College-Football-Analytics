"""V2 historical schema regression tests; no V1 runtime behavior changes."""
import pytest

from cfb_analytics.historical import HistoricalGame, utc_instant, validate_unique_games


def game(**overrides):
    values = dict(season=2025, game_id=42, home="Texas", away="Oklahoma",
                  home_division="FBS", away_division="FBS",
                  kickoff="2025-10-11T19:00:00Z",
                  source_retrieved_at="2025-10-11T15:00:00-04:00",
                  source="CFBD", home_score=28, away_score=14)
    values.update(overrides)
    return HistoricalGame(**values)


def test_fbs_accuracy_and_provenance():
    record = game(source_retrieved_at="2025-10-11T14:00:00-04:00")
    assert record.classification == "fbs_vs_fbs"
    assert record.eligible_fbs_accuracy
    assert record.verified_pregame("2025-10-11T18:59:59Z", "2025-10-11T17:00:00Z")
    assert not record.verified_pregame("2025-10-11T19:00:00Z", "2025-10-11T17:00:00Z")
    assert not record.verified_pregame("2025-10-11T17:00:00Z", "2025-10-11T18:00:00Z")


def test_fcs_context_not_fbs_accuracy():
    record = game(away_division="FCS")
    assert record.classification == "fbs_vs_fcs"
    assert not record.eligible_fbs_accuracy


def test_unknown_division_never_counted():
    assert not game(away_division="UNKNOWN").eligible_fbs_accuracy


def test_missing_or_tied_score_not_scored():
    assert not game(home_score=None, away_score=None).eligible_fbs_accuracy
    assert not game(home_score=14, away_score=14).eligible_fbs_accuracy


@pytest.mark.parametrize("changes", [
    {"kickoff": "2025-10-11T19:00:00"},
    {"source_retrieved_at": "bad"},
    {"source": ""},
    {"away": "Texas"},
    {"home_score": -1},
    {"home_score": 3, "away_score": None},
    {"home_division": "NFL"},
    {"schema_version": 2},
])
def test_invalid_records_rejected(changes):
    with pytest.raises(ValueError):
        game(**changes)


def test_duplicate_ids_scoped_by_season():
    validate_unique_games([game(), game(season=2024)])
    with pytest.raises(ValueError):
        validate_unique_games([game(), game()])


def test_utc_requires_timezone():
    assert utc_instant("2025-10-11T15:00:00-04:00") == utc_instant("2025-10-11T19:00:00Z")
    assert utc_instant("2025-10-11T19:00:00") is None


def test_game_download_after_kickoff_does_not_affect_forecast_provenance():
    record = game(source_retrieved_at="2025-10-12T00:00:00Z")
    assert record.verified_pregame("2025-10-11T18:00:00Z", "2025-10-11T17:00:00Z")
    assert not record.verified_pregame("2025-10-11T18:00:00Z")
