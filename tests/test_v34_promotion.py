from cfb_analytics.historical import HistoricalGame
from cfb_analytics.historical_evaluation import ArchivedForecast
from cfb_analytics.v34_promotion import promotion_gate


def game(season, game_id, home_score=21, away_score=14):
    return HistoricalGame(season=season, game_id=game_id, home="Georgia", away="Alabama",
                          home_division="FBS", away_division="FBS",
                          kickoff=f"{season}-09-02T12:00:00Z",
                          source_retrieved_at=f"{season}-09-03T12:00:00Z",
                          source="CFBD", home_score=home_score, away_score=away_score)


def forecast(season, game_id, p, timestamp=None):
    return ArchivedForecast(season=season, game_id=game_id,
                            home_win_probability=p,
                            generated_at=timestamp or f"{season}-09-01T12:00:00Z",
                            input_retrieved_at=f"{season}-08-31T12:00:00Z")


def test_no_promotion_for_small_or_single_season_sample():
    games = [game(2024, n) for n in range(1, 21)]
    base = [forecast(2024, n, 0.55) for n in range(1, 21)]
    challenger = [forecast(2024, n, 0.9) for n in range(1, 21)]
    result = promotion_gate(games, base, challenger)
    assert result["brier_delta"] < 0
    assert result["decision"] == "retain_champion"


def test_promotion_gate_requires_matched_pregame_provenance():
    games = [game(2024, 1), game(2025, 2)]
    base = [forecast(2024, 1, 0.5), forecast(2025, 2, 0.5)]
    candidate = [forecast(2024, 1, 0.8), forecast(2025, 2, 0.8,
                                                timestamp="2025-09-03T12:00:00Z")]
    result = promotion_gate(games, base, candidate, min_games=1)
    assert result["matched_games"] == 1
    assert result["excluded"]["not_verified_pregame"] == 1
    assert result["decision"] == "retain_champion"
