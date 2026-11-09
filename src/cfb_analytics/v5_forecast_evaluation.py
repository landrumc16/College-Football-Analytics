"""Evaluate frozen pregame forecasts against finalized outcomes.

The evaluator only scores archived, timestamped predictions. Retrospective
ratings and outcomes cannot be substituted for a pregame prediction archive.
No challenger promotion or production model changes occur here.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from math import isfinite, log


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Timestamp must be ISO-8601 with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def evaluate_archived_forecasts(rows: list[dict], bins: int = 10) -> dict:
    """Score uniquely identified, timestamped, settled binary outcomes.

    Required: game_id, model_id, prediction_time, kickoff_time,
    home_win_probability, home_won. Predictions must predate kickoff.
    One frozen forecast per game and model is permitted. Games without
    final results are not eligible and must not be passed to this function.
    """
    if not isinstance(rows, list):
        raise ValueError("Forecast archive must be an array")
    if not isinstance(bins, int) or isinstance(bins, bool) or bins < 2 or bins > 100:
        raise ValueError("Invalid calibration bin count")
    by_model = defaultdict(list)
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid forecast row")
        game = row.get("game_id")
        model = row.get("model_id")
        if not isinstance(game, str) or not game.strip() or not isinstance(model, str) or not model.strip():
            raise ValueError("Missing game or model identity")
        key = (game, model)
        if key in seen:
            raise ValueError("Duplicate game-model archived forecast")
        seen.add(key)
        forecast_at = _timestamp(row.get("prediction_time"))
        kickoff_at = _timestamp(row.get("kickoff_time"))
        if forecast_at >= kickoff_at:
            raise ValueError("Forecast is not pregame")
        p = row.get("home_win_probability")
        outcome = row.get("home_won")
        if not isinstance(p, (int, float)) or isinstance(p, bool) or not isfinite(p) or not 0 <= p <= 1:
            raise ValueError("Invalid win probability")
        if not isinstance(outcome, bool):
            raise ValueError("Final home-win outcome must be boolean")
        by_model[model].append((float(p), int(outcome)))
    models = {}
    for model, predictions in sorted(by_model.items()):
        count = len(predictions)
        brier = sum((p - y) ** 2 for p, y in predictions) / count
        logloss = -sum(y * log(max(p, 1e-15)) + (1 - y) * log(max(1 - p, 1e-15))
                       for p, y in predictions) / count
        correct = sum((p >= .5) == bool(y) for p, y in predictions)
        groups = [[] for _ in range(bins)]
        for p, y in predictions:
            groups[min(int(p * bins), bins - 1)].append((p, y))
        models[model] = {
            "games": count,
            "brier": brier,
            "logloss": logloss,
            "accuracy": correct / count,
            "calibration": [
                {"bin": i, "games": len(group),
                 "mean_predicted": sum(p for p, _ in group) / len(group) if group else None,
                 "observed_home_win_rate": sum(y for _, y in group) / len(group) if group else None}
                for i, group in enumerate(groups)
            ],
        }
    return {
        "status": "verified_archive_inputs_required",
        "models": models,
        "total_forecasts": len(seen),
        "predictive_promotion_authorized": False,
        "limitations": [
            "Scores are valid only if archived timestamps and final outcomes are independently verified",
            "Cross-model comparisons require identical game coverage",
            "No retrospective prediction may be presented as a frozen pregame forecast",
        ],
    }
