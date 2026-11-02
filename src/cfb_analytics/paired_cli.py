"""Command-line matched benchmark of two independent archived pregame forecasts.

Inputs use the same JSON arrays as historical_cli.py. The workbook input must
contain model-only probabilities, never market-assisted display probabilities.
"""
import argparse
import json
from pathlib import Path

from .historical import HistoricalGame
from .historical_evaluation import ArchivedForecast
from .paired_benchmark import paired_scorecard


def run(games_path: Path, workbook_path: Path, candidate_path: Path) -> dict:
    def load(path, record_type):
        rows = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError(f"{path} must contain a JSON array")
        return [record_type(**row) for row in rows]

    return paired_scorecard(
        load(games_path, HistoricalGame),
        load(workbook_path, ArchivedForecast),
        load(candidate_path, ArchivedForecast),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score matched archived model predictions")
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run(args.games, args.workbook, args.candidate)
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
