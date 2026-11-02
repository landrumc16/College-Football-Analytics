"""Leakage-aware matched-game scoring for V3 research candidates.

This evaluates supplied forecasts; it does not manufacture pregame provenance.
"""
from __future__ import annotations

from collections import defaultdict
from math import log
from statistics import mean

from .historical import HistoricalGame, validate_unique_games, utc_instant
from .historical_evaluation import ArchivedForecast

_EPS = 1e-12


def _metrics(rows: list[tuple[float, int]]) -> dict:
    if not rows:
        return {"games": 0, "accuracy": None, "brier": None, "logloss": None,
                "calibration": []}
    bins: dict[int, list[tuple[float, int]]] = defaultdict(list)
    for p, outcome in rows:
        bins[min(9, int(p * 10))].append((p, outcome))
    return {
        "games": len(rows),
        "accuracy": mean((p >= .5) == bool(y) for p, y in rows),
        "brier": mean((p - y) ** 2 for p, y in rows),
        "logloss": mean(-y * log(max(_EPS, p)) -
                        (1 - y) * log(max(_EPS, 1 - p)) for p, y in rows),
        "calibration": [
            {"bin": i, "games": len(group),
             "mean_predicted": mean(p for p, _ in group),
             "observed": mean(y for _, y in group)}
            for i, group in sorted(bins.items())
        ],
    }


def evaluate_matched(games: list[HistoricalGame],
                     baseline: dict[tuple[int, int], tuple[float, str, str]],
                     candidate: dict[tuple[int, int], tuple[float, str, str]],
                     *, holdout_seasons: tuple[int, ...] = (2025,)) -> dict:
    """Forecast maps: (season, game_id) -> (P(home wins), generated_at, input_retrieved_at).

    All comparisons use exactly matched games and require independently valid
    pregame forecast and input timestamps. Scores cannot be sourced from games
    without final non-tied results. Holdout seasons are reported separately.
    """
    validate_unique_games(games)
    if not holdout_seasons:
        raise ValueError("At least one holdout season required")
    groups: dict[str, dict[str, list[tuple[float, int]]]] = defaultdict(
        lambda: {"baseline": [], "candidate": []})
    exclusions: dict[str, int] = defaultdict(int)
    for game in sorted(games, key=lambda g: (utc_instant(g.kickoff), g.game_id)):
        key = (game.season, game.game_id)
        if game.classification not in ("fbs_vs_fbs", "fbs_vs_fcs"):
            exclusions["other_division"] += 1
            continue
        if game.home_score is None or game.away_score is None or game.home_score == game.away_score:
            exclusions["missing_or_tied_score"] += 1
            continue
        if key not in baseline or key not in candidate:
            exclusions["unmatched"] += 1
            continue
        entries = (baseline[key], candidate[key])
        if any(not isinstance(p, (float, int)) or isinstance(p, bool) or not 0 <= p <= 1
               for p, _, _ in entries):
            exclusions["invalid_probability"] += 1
            continue
        if any(not game.verified_pregame(generated, retrieved)
               for _, generated, retrieved in entries):
            exclusions["invalid_pregame_provenance"] += 1
            continue
        split = "holdout" if game.season in holdout_seasons else "development"
        outcome = int(game.home_score > game.away_score)
        for label, (p, _, _) in zip(("baseline", "candidate"), entries):
            value = (float(p), outcome)
            groups[f"{split}/all"][label].append(value)
            groups[f"{split}/{game.classification}"][label].append(value)
            groups[f"{split}/{game.season}"][label].append(value)
    return {
        "type": "matched_archived_pregame_comparison",
        "holdout_seasons": list(holdout_seasons),
        "groups": {name: {model: _metrics(rows) for model, rows in models.items()}
                   for name, models in sorted(groups.items())},
        "exclusions": dict(sorted(exclusions.items())),
        "note": "No retrospective predictions are treated as archived pregame forecasts.",
    }
