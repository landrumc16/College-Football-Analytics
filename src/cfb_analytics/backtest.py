"""Leakage-free chronological evaluation of the rating model.

Each game is predicted using only results from earlier weeks. Games within
the same week are predicted from the same pre-week snapshot.
"""
import argparse
import json
from math import log
from pathlib import Path

from .model import ModelSettings, win_probability_from_rating_gap
from .ratings import Game, Team, calculate_ratings


def backtest_weeks(teams: list[Team], games: list[Game],
                   settings: ModelSettings = ModelSettings()) -> dict:
    if not teams:
        raise ValueError("At least one team is required")
    if any(g.week <= 0 for g in games):
        raise ValueError("Every historical game needs a positive week")
    known = {team.name for team in teams}
    if len(known) != len(teams):
        raise ValueError("Duplicate team names")
    priors = {t.name: settings.prior_year_weight * t.prior for t in teams}
    history = []
    scored = []
    weekly = []
    weekly_diagnostics = []
    for week in sorted({game.week for game in games}):
        ratings = calculate_ratings(teams, history, settings)
        week_start = len(scored)
        for game in (g for g in games if g.week == week):
            if game.home not in known and game.away not in known:
                continue
            home = (ratings[game.home].adaptive_rating if game.home in known
                    else settings.fcs_opponent_rating)
            away = (ratings[game.away].adaptive_rating if game.away in known
                    else settings.fcs_opponent_rating)
            gap = home - away + settings.home_field_advantage
            probability = win_probability_from_rating_gap(
                gap, settings.win_probability_scale)
            actual = int(game.home_score > game.away_score)
            if game.home_score == game.away_score:
                raise ValueError("Historical completed games cannot be tied")
            # Apply preseason weighting to FBS priors only. FCS opponents
            # retain the same fixed rating used by the evolving model.
            prior_home = priors.get(game.home, settings.fcs_opponent_rating)
            prior_away = priors.get(game.away, settings.fcs_opponent_rating)
            baseline = win_probability_from_rating_gap(
                prior_home - prior_away + settings.home_field_advantage,
                settings.win_probability_scale)
            scored.append((probability, baseline, actual))
        if len(scored) > week_start:
            batch = scored[week_start:]
            weekly.append({"week": week, "games": len(batch)})
            weekly_diagnostics.append({
                "week": week,
                "games": len(batch),
                "model_brier": sum((p - y) ** 2 for p, _, y in batch) / len(batch),
                "baseline_brier": sum((b - y) ** 2 for _, b, y in batch) / len(batch),
                "model_winner_accuracy": sum((p >= 0.5) == bool(y) for p, _, y in batch) / len(batch),
                "baseline_winner_accuracy": sum((b >= 0.5) == bool(y) for _, b, y in batch) / len(batch),
            })
        history.extend(g for g in games if g.week == week)
    if not scored:
        return {"games": 0, "model": None, "preseason_baseline": None}

    def metrics(index):
        probabilities = [row[index] for row in scored]
        n = len(scored)
        return {
            "winner_accuracy": sum((p >= 0.5) == bool(y)
                                   for p, (_, _, y) in zip(probabilities, scored)) / n,
            "brier_score": sum((p - y) ** 2
                               for p, (_, _, y) in zip(probabilities, scored)) / n,
            "log_loss": -sum(y * log(max(1e-15, p)) +
                             (1-y) * log(max(1e-15, 1-p))
                             for p, (_, _, y) in zip(probabilities, scored)) / n,
        }
    model = metrics(0)
    baseline = metrics(1)
    return {
        "games": len(scored),
        "model": model,
        "preseason_baseline": baseline,
        "improvement_vs_preseason": {
            "winner_accuracy_percentage_points":
                100 * (model["winner_accuracy"] - baseline["winner_accuracy"]),
            "brier_score_reduction": baseline["brier_score"] - model["brier_score"],
            "log_loss_reduction": baseline["log_loss"] - model["log_loss"],
        },
        "weekly_coverage": weekly,
        "weekly_diagnostics": weekly_diagnostics,
        "evaluation_scope": "2026 frozen completed games; weekly pregame snapshots",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Leakage-free weekly backtest on frozen workbook games")
    parser.add_argument("--output", type=Path, help="Optional JSON results file")
    args = parser.parse_args(argv)
    from .parity import load_baseline
    roster, results = load_baseline()
    teams = [Team(t["name"], t["conference"], t["prior"]) for t in roster]
    games = [Game(g["home"], g["away"], g["home_score"],
                  g["away_score"], g["week"]) for g in results]
    if len(teams) != 138 or len(games) != 510:
        parser.error(f"Incomplete historical fixture: {len(teams)} teams, {len(games)} games")
    report = backtest_weeks(teams, games)
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
