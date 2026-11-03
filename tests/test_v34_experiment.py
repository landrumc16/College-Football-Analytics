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
