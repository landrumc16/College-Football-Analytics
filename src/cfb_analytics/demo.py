"""Build a reproducible sample report using the frozen 2026 baseline.

This is a demonstration snapshot, NOT current live CFBD data.
Usage: python -m cfb_analytics.demo
"""
import json
from pathlib import Path

from .parity import load_baseline
from .pipeline import build_season_report


def main():
    roster, completed = load_baseline()
    folder = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
    schedule = []
    for path in sorted(folder.glob("2026-week7-schedule-[0-9][0-9].json")):
        schedule.extend(json.loads(path.read_text(encoding="utf-8")))
    if len(schedule) != 888:
        raise RuntimeError("Incomplete frozen schedule")
    scored = {}
    for game in completed:
        key = (game["home"], game["away"])
        if key in scored:
            raise ValueError(f"Duplicate completed matchup {key}")
        scored[key] = game
    records = []
    for index, game in enumerate(schedule, 1):
        match = scored.get((game["home"], game["away"]))
        if game["completed"] and match is None:
            raise ValueError(f"Missing result for completed game {game}")
        records.append({
            "game_id": index, "season": 2026, "week": game["week"],
            "home": game["home"], "away": game["away"],
            "completed": game["completed"],
            "home_score": match["home_score"] if match else None,
            "away_score": match["away_score"] if match else None,
            "neutral_site": False,
        })
    report = build_season_report(
        {"season": 2026, "source": "FROZEN 2026 WEEK 7 DEMO - NOT LIVE",
         "games": records},
        roster,
    )
    output = Path("web/public/season-report.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}: {report['summary']}")


if __name__ == "__main__":
    main()
