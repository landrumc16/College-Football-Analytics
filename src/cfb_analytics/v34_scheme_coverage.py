"""As-of matchup coverage report for source-backed team scheme metrics.

This is a data-availability diagnostic, not an accuracy or betting-edge claim.
"""
from .v34_matchups import matchup_scheme_diagnostics


def scheme_coverage_report(games, schemes, *, cutoff_by_game):
    report = matchup_scheme_diagnostics(games, schemes, cutoff_by_game=cutoff_by_game)
    matchups = report["matchups"]
    count = len(matchups)
    covered = sum(x["covered_metrics"] > 0 for x in matchups)
    complete = sum(x["missing_metrics"] == 0 for x in matchups)
    per_metric = {}
    for match in matchups:
        for comparison in match["comparisons"]:
            name = comparison["feature"]
            per_metric[name] = per_metric.get(name, 0) + 1
    return {"games_evaluated": count, "games_with_any_scheme_comparison": covered,
            "games_with_all_scheme_comparisons": complete,
            "coverage_fraction": covered/count if count else None,
            "metric_game_counts": dict(sorted(per_metric.items())),
            "scope": "pre-kickoff source-backed scheme coverage; not prediction accuracy"}
