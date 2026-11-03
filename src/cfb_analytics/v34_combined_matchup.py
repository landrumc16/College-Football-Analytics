"""Combine independently dated roster, scheme and coaching matchup research.

No model score or inferred missing features are produced.
"""
from .v34_talent_matchups import talent_matchup_report
from .v34_coaching_matchup import coaching_matchup_report


def combined_matchup_report(games, talent, staff, schemes, *, cutoff_by_game,
                            prior_cutoff_by_game):
    talent_rows = talent_matchup_report(games, talent, cutoff_by_game=cutoff_by_game)["matchups"]
    coaching_rows = coaching_matchup_report(games, staff, schemes,
                      cutoff_by_game=cutoff_by_game,
                      prior_cutoff_by_game=prior_cutoff_by_game)["matchups"]
    if [r["game_id"] for r in talent_rows] != [r["game_id"] for r in coaching_rows]:
        raise ValueError("Matchup alignment mismatch")
    combined = []
    for roster, coaching in zip(talent_rows, coaching_rows):
        combined.append({"game_id": roster["game_id"], "home": roster["home"],
                         "away": roster["away"],
                         "talent_comparisons": roster["comparisons"],
                         "scheme_comparisons": coaching["comparisons"],
                         "home_staff": coaching["home_staff"],
                         "away_staff": coaching["away_staff"],
                         "talent_features_covered": roster["covered_features"],
                         "scheme_metrics_covered": coaching["covered_metrics"]})
    return {"matchups": combined,
            "scope": "descriptive as-of roster, coaching and scheme features; no model promotion"}
