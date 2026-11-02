"""Research-only paired walk-forward experiments against the frozen incumbent.

These experiments use the same completed historical games and pre-week information
for each candidate. They are retrospective, not archived pregame forecasts.
No candidate is automatically promoted to the live model.
"""
import argparse
import json
from dataclasses import replace
from pathlib import Path

from .backtest import backtest_weeks
from .model import ModelSettings
from .ratings import Game, Team


CANDIDATES = {
    "home_field_0": {"home_field_advantage": 0.0},
    "home_field_2": {"home_field_advantage": 2.0},
    "home_field_4": {"home_field_advantage": 4.0},
    "probability_scale_15": {"win_probability_scale": 15.0},
    "probability_scale_21": {"win_probability_scale": 21.0},
    "prior_weight_075": {"prior_year_weight": 0.75},
    "ridge_strength_7": {"ridge_strength": 7.0},
    "fcs_rating_minus_20": {"fcs_opponent_rating": -20.0},
}


def compare_candidates(teams: list[Team], games: list[Game],
                       settings: ModelSettings = ModelSettings()) -> dict:
    incumbent = backtest_weeks(teams, games, settings)
    experiments = {}
    for name, overrides in CANDIDATES.items():
        candidate = backtest_weeks(teams, games, replace(settings, **overrides))
        if candidate["games"] != incumbent["games"]:
            raise ValueError("Candidate and incumbent evaluated different game counts")
        if incumbent["games"]:
            base = incumbent["model"]
            trial = candidate["model"]
            delta = {
                "brier_reduction": base["brier_score"] - trial["brier_score"],
                "log_loss_reduction": base["log_loss"] - trial["log_loss"],
                "winner_accuracy_percentage_points":
                    100 * (trial["winner_accuracy"] - base["winner_accuracy"]),
            }
        else:
            delta = None
        experiments[name] = {
            "overrides": overrides,
            "games": candidate["games"],
            "model": candidate["model"],
            "delta_vs_incumbent": delta,
            "matchup_diagnostics": candidate.get("matchup_diagnostics"),
        }
    return {
        "evaluation_type": "retrospective_preweek_replay",
        "holdout_validated": False,
        "promotion_authorized": False,
        "games": incumbent["games"],
        "incumbent": incumbent["model"],
        "candidates": experiments,
        "disclaimer": "Exploratory same-sample comparison only. No tuning or model promotion without separate season holdouts.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exploratory walk-forward candidate comparison")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    from .parity import load_baseline
    roster, results = load_baseline()
    teams = [Team(t["name"], t["conference"], t["prior"]) for t in roster]
    games = [Game(g["home"], g["away"], g["home_score"], g["away_score"], g["week"]) for g in results]
    report = compare_candidates(teams, games)
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
