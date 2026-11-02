"""V3 archived pregame comparison CLI; rejects duplicate forecasts and missing provenance."""
import argparse
import json
from pathlib import Path

from .historical import HistoricalGame
from .historical_evaluation import ArchivedForecast
from .v3_evaluation import evaluate_matched


def _load(path, cls):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON array")
    return [cls(**row) for row in data]


def _index(forecasts):
    indexed = {}
    for f in forecasts:
        key = (f.season, f.game_id)
        if key in indexed:
            raise ValueError(f"Duplicate forecast {key}")
        indexed[key] = (f.home_win_probability, f.generated_at, f.input_retrieved_at)
    return indexed


def run(games_path, baseline_path, candidate_path, holdout_seasons=(2025,)):
    games = _load(Path(games_path), HistoricalGame)
    baseline = _index(_load(Path(baseline_path), ArchivedForecast))
    candidate = _index(_load(Path(candidate_path), ArchivedForecast))
    return evaluate_matched(games, baseline, candidate, holdout_seasons=tuple(holdout_seasons))


def main(argv=None):
    parser = argparse.ArgumentParser(description="V3 leakage-checked matched archived forecast evaluation")
    parser.add_argument("--games", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--holdout-season", type=int, action="append", default=None)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run(args.games, args.baseline, args.candidate, args.holdout_season or [2025])
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
