"""V2 historical adapter must not fabricate historical division membership."""
import pytest

from cfb_analytics.ingestion import normalize_cfbd_games
from cfb_analytics.historical_adapter import historical_from_ingested


def fixture():
    return normalize_cfbd_games([{
        "id": 12, "season": 2024, "week": 1,
        "homeTeam": "FBS A", "awayTeam": "FCS B",
        "homePoints": 28, "awayPoints": 10,
        "startDate": "2024-08-31T20:00:00Z",
    }], 2024)


def test_adapter_retains_fcs_game_as_context():
    records = historical_from_ingested(
        fixture(), retrieved_at="2024-09-01T00:00:00Z",
        source="CFBD", divisions_by_season={2024: {"FBS A": "FBS", "FCS B": "FCS"}})
    assert len(records) == 1
    assert records[0].classification == "fbs_vs_fcs"
    assert records[0].home_score == 28
    assert not records[0].eligible_fbs_accuracy


def test_missing_opponent_classification_is_not_assumed_fbs():
    records = historical_from_ingested(
        fixture(), retrieved_at="2024-09-01T00:00:00Z",
        source="CFBD", divisions_by_season={2024: {"FBS A": "FBS"}})
    assert records[0].away_division == "UNKNOWN"
    assert not records[0].eligible_fbs_accuracy


def test_missing_season_roster_rejected():
    with pytest.raises(ValueError, match="season-specific"):
        historical_from_ingested(
            fixture(), retrieved_at="2024-09-01T00:00:00Z",
            source="CFBD", divisions_by_season={2025: {"FBS A": "FBS"}})


def test_missing_kickoff_rejected():
    games = normalize_cfbd_games([{
        "id": 12, "season": 2024, "week": 1,
        "homeTeam": "FBS A", "awayTeam": "FCS B",
        "homePoints": 28, "awayPoints": 10,
    }], 2024)
    with pytest.raises(ValueError, match="kickoff"):
        historical_from_ingested(
            games, retrieved_at="2024-09-01T00:00:00Z",
            source="CFBD", divisions_by_season={2024: {"FBS A": "FBS"}})
