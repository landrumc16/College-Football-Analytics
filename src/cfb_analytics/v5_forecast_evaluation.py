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
    by_game = defaultdict(dict)
    game_kickoffs = {}
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
        if game in game_kickoffs and game_kickoffs[game] != kickoff_at:
            raise ValueError("Conflicting kickoff times for game")
        game_kickoffs[game] = kickoff_at
        p = row.get("home_win_probability")
        outcome = row.get("home_won")
        if not isinstance(p, (int, float)) or isinstance(p, bool) or not isfinite(p) or not 0 <= p <= 1:
            raise ValueError("Invalid win probability")
        if not isinstance(outcome, bool):
            raise ValueError("Final home-win outcome must be boolean")
        by_model[model].append((float(p), int(outcome)))
        if game in by_game and any(existing_outcome != outcome for _, existing_outcome in by_game[game].values()):
            raise ValueError("Conflicting final outcomes for game")
        by_game[game][model] = (float(p), outcome)
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
    comparisons = []
    model_names = sorted(by_model)
    for i, left in enumerate(model_names):
        for right in model_names[i + 1:]:
            matched = [(models[left], models[right]) for models in by_game.values() if left in models and right in models]
            if not matched:
                continue
            def paired_metrics(index):
                brier = sum((pair[index][0] - int(pair[index][1])) ** 2 for pair in matched) / len(matched)
                logloss = -sum(int(pair[index][1]) * log(max(pair[index][0], 1e-15)) +
                               (1 - int(pair[index][1])) * log(max(1 - pair[index][0], 1e-15))
                               for pair in matched) / len(matched)
                return brier, logloss
            a_brier, a_logloss = paired_metrics(0)
            b_brier, b_logloss = paired_metrics(1)
            comparisons.append({"model_a": left, "model_b": right, "matched_games": len(matched),
                                "model_a_brier": a_brier, "model_b_brier": b_brier,
                                "model_a_logloss": a_logloss, "model_b_logloss": b_logloss,
                                "scope": "paired_games_only_no_promotion_claim"})
    return {
        "status": "verified_archive_inputs_required",
        "paired_baseline_comparisons": comparisons,
        "models": models,
        "total_forecasts": len(seen),
        "predictive_promotion_authorized": False,
        "limitations": [
            "Scores are valid only if archived timestamps and final outcomes are independently verified",
            "Cross-model comparisons require identical game coverage",
            "No retrospective prediction may be presented as a frozen pregame forecast",
        ],
    }


def main() -> None:
    """Score a supplied independently verified frozen archive without publishing it."""
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True,
                        help="JSON array of frozen pregame forecasts with verified final outcomes")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.archive.read_text(encoding="utf-8"))
    report = evaluate_archived_forecasts(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
