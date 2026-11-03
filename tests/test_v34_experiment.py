import pytest
from cfb_analytics.v34_experiment import evaluate_feature_challenger


def test_feature_experiment_requires_explicit_cutoff_per_game():
    class Game:
        season = 2025
        game_id = 123
    with pytest.raises(ValueError, match="cutoff"):
        evaluate_feature_challenger([Game()], [], [], [], [], [], {})


def test_empty_feature_inputs_do_not_fabricate_coverage():
    result = evaluate_feature_challenger([], [], [], [], [], [], {})
    assert result["feature_coverage"] == {
        "games": 0, "talent_team_features": 0,
        "coaching_assignments": 0, "scheme_team_features": 0}
    assert result["promotion_status"] == "research_only_manual_validation_required"


def test_coverage_only_counts_matchup_participants_and_rejects_postkickoff():
    from cfb_analytics.historical import HistoricalGame
    game = HistoricalGame(season=2025, game_id=123, home="Georgia", away="Alabama",
                          home_division="FBS", away_division="FBS",
                          kickoff="2025-09-02T12:00:00Z",
                          source_retrieved_at="2025-09-03T00:00:00Z", source="CFBD",
                          home_score=21, away_score=14)
    observed = {"feature": "high_school_recruiting", "value": 90,
                "source": "published recruiting ranking",
                "observed_at": "2025-07-01T00:00:00Z",
                "published_at": "2025-07-02T00:00:00Z"}
    rows = [{**observed, "team": team} for team in ("Georgia", "Alabama", "Ohio State")]
    result = evaluate_feature_challenger([game], [], [], rows, [], [],
                                         {(2025, 123): "2025-09-01T12:00:00Z"})
    assert result["feature_coverage"]["talent_team_features"] == 2
    with pytest.raises(ValueError, match="precede kickoff"):
        evaluate_feature_challenger([game], [], [], rows, [], [],
                                    {(2025, 123): "2025-09-03T12:00:00Z"})
