"""Leakage-safe, paired feature experiment for the existing V3.3 benchmark.

Research only. Predictions are supplied by the caller, never synthesized from
final scores. Feature coverage is reported rather than silently imputed.
"""
from .talent import features_as_of
from .coaching import coaching_as_of, scheme_as_of
from .paired_benchmark import paired_scorecard


def evaluate_feature_challenger(games, champion, challenger, observations,
                                coaching, schemes, cutoff_by_game):
    """Compare archived forecasts on identical games and report input coverage.

    cutoff_by_game maps (season, game_id) to the prediction-time cutoff.
    Missing cutoffs fail closed; no postgame feature can be used for evaluation.
    """
    keys = {(g.season, g.game_id) for g in games}
    if keys != set(cutoff_by_game):
        raise ValueError("Every game needs exactly one explicit prediction cutoff")
    coverage = {"games": len(games), "talent_team_features": 0,
                "coaching_assignments": 0, "scheme_team_features": 0}
    # Feature data is deliberately not passed into the scoring algorithm.
    # The challenger probabilities must have been archived before kickoff.
    for game in games:
        cutoff = cutoff_by_game[(game.season, game.game_id)]
        talent = features_as_of(observations, cutoff)
        staff = coaching_as_of(coaching, cutoff)
        tendencies = scheme_as_of(schemes, cutoff)
        coverage["talent_team_features"] += len(talent)
        coverage["coaching_assignments"] += len(staff)
        coverage["scheme_team_features"] += len(tendencies)
    return {"paired": paired_scorecard(games, champion, challenger),
            "feature_coverage": coverage,
            "promotion_status": "research_only_manual_validation_required"}
