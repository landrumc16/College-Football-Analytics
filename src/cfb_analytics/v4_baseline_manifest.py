"""Immutable-by-content V4 baseline manifest; does not imply four-season evidence."""
import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from .model import ModelSettings
from .parity import load_baseline


def build_manifest(root: Path) -> dict:
    fixtures = sorted((root / "tests" / "fixtures").glob("2026-week7-*.json"))
    if not fixtures:
        raise ValueError("Frozen baseline fixture files not found")
    teams, games = load_baseline(root / "tests" / "fixtures")
    if len(teams) != 138 or len(games) != 510:
        raise ValueError("Frozen baseline roster/game counts differ from contract")
    files = [{"path": str(p.relative_to(root)),
              "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
             for p in fixtures]
    model_paths = ["src/cfb_analytics/model.py",
                   "src/cfb_analytics/ratings.py",
                   "src/cfb_analytics/backtest.py",
                   "src/cfb_analytics/parity.py"]
    source = [{"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()}
              for path in model_paths]
    return {
        "schema_version": 1,
        "label": "2026 frozen spreadsheet retrospective baseline",
        "evaluation_type": "retrospective_weekly_as_of",
        "historical_seasons": [2026],
        "eligible_for_v4_multiseason_release_gate": False,
        "fbs_team_count": len(teams),
        "completed_fixture_games": len(games),
        "settings": asdict(ModelSettings()),
        "fixture_hashes": files,
        "incumbent_source_hashes": source,
        "limitations": [
            "One frozen 2026 season, not four independent held-out seasons",
            "Retrospective pre-week calculations, not immutable prospective forecasts",
            "No challenger performance demonstrated",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_manifest(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"fixture_files": len(report["fixture_hashes"]),
                      "source_files": len(report["incumbent_source_hashes"]),
                      "seasons": report["historical_seasons"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
