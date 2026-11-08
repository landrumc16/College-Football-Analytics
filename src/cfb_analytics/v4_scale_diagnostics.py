"""Cross-season comparability diagnostics for retrospective season ratings.

Standardization is a research diagnostic, not independent validation of the
underlying schedule-adjusted rating scale or authorization to publish rankings.
"""
from __future__ import annotations

from math import isfinite, sqrt


def compare_season_scales(reports: list[dict], *, minimum_teams: int = 20) -> dict:
    if not isinstance(minimum_teams, int) or isinstance(minimum_teams, bool) or minimum_teams < 2:
        raise ValueError("minimum_teams must be at least two")
    if not reports:
        raise ValueError("No historical season ratings")
    years = set()
    results = []
    for report in sorted(reports, key=lambda item: item["season"]):
        season = report.get("season")
        if not isinstance(season, int) or isinstance(season, bool) or season in years:
            raise ValueError("Duplicate or invalid season")
        years.add(season)
        if report.get("status") != "retrospective_schedule_adjusted_research_only":
            raise ValueError("Unreviewed rating type")
        teams = report.get("teams")
        if not isinstance(teams, list):
            raise ValueError("Missing team ratings")
        seen = set()
        values = []
        for row in teams:
            team, rating = row.get("team"), row.get("rating")
            if not isinstance(team, str) or not team.strip() or team in seen:
                raise ValueError("Invalid or duplicate team")
            seen.add(team)
            if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not isfinite(rating):
                raise ValueError("Invalid rating")
            values.append(float(rating))
        if len(values) < minimum_teams:
            raise ValueError(f"Insufficient season team coverage: {season}")
        mean = sum(values) / len(values)
        sd = sqrt(sum((v - mean) ** 2 for v in values) / len(values))
        if sd <= 0:
            raise ValueError(f"Degenerate season strength distribution: {season}")
        results.append({
            "season": season,
            "team_count": len(values),
            "mean_rating": round(mean, 6),
            "population_sd": round(sd, 6),
            "min_rating": round(min(values), 6),
            "max_rating": round(max(values), 6),
            "source_comparable_verified": False,
        })
    return {
        "status": "cross_season_scale_diagnostic_only",
        "season_count": len(results),
        "seasons": results,
        "program_rankings_publishable": False,
        "limitations": [
            "Within-season Elo starts each year at 1500 and has not been calibrated for season-to-season comparability",
            "Different season schedules, FBS membership, 2020 disruption and opponent pools can change rating distributions",
            "Distribution standardization alone does not establish comparable opponent-adjusted program strengths",
            "Retrospective final-score ratings are not pregame features or independently validated predictions",
        ],
    }


def main() -> None:
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("--ratings", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.ratings.read_text())
    report = compare_season_scales(data["seasons"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
