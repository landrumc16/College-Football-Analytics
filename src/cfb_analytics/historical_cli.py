"""Version 2 historical evaluation CLI.

Reads versioned records and *archived* forecasts; does not create forecasts
retroactively from game outcomes.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .historical import HistoricalGame
from .historical_evaluation import ArchivedForecast, evaluate_forecasts


def run(games_path: Path, forecasts_path: Path) -> dict:
    game_data = json.loads(games_path.read_text(encoding="utf-8"))
    forecast_data = json.loads(forecasts_path.read_text(encoding="utf-8"))
    if not isinstance(game_data, list) or not isinstance(forecast_data, list):
        raise ValueError("Inputs must be JSON arrays")
    games = [HistoricalGame(**row) for row in game_data]
    forecasts = [ArchivedForecast(**row) for row in forecast_data]
    result = evaluate_forecasts(games, forecasts)
    result["historical_records"] = len(games)
    result["archived_forecasts"] = len(forecasts)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate verified pregame forecasts")
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--forecasts", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run(args.games, args.forecasts)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
