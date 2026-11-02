"""Summarize bounded V3 Elo study without using holdout to select a model.

This is research evidence, not a production promotion decision.
"""
import argparse
import json
from pathlib import Path


def summarize(study):
    if study.get("type") != "v3_retrospective_elo_sensitivity":
        raise ValueError("Unexpected study type")
    if study.get("holdout_is_not_used_for_selection") is not True:
        raise ValueError("Holdout isolation is required")
    incumbent = study["incumbent"]
    selected = study["selected"]
    candidates = study["candidates"]
    if len(candidates) != 5:
        raise ValueError("Expected five predeclared candidates")
    for row in candidates:
        if not row["development"]["games"] or not row["holdout"]["games"]:
            raise ValueError("Development and holdout must both contain scored games")
    if (incumbent["k"], incumbent["home_advantage"]) != (24, 55):
        raise ValueError("Incumbent parameters changed")
    if selected["development"]["brier"] != min(c["development"]["brier"] for c in candidates):
        raise ValueError("Selected candidate does not minimize development Brier")
    development_delta = incumbent["development"]["brier"] - selected["development"]["brier"]
    holdout_delta = incumbent["holdout"]["brier"] - selected["holdout"]["brier"]
    # Minimum practical effect avoids recommending a switch on negligible gains.
    meaningful = development_delta >= 0.001 and holdout_delta >= 0.001
    return {
        "type": "v3_elo_research_decision",
        "study_type": study["type"],
        "holdout_season": study["holdout_season"],
        "selected_parameters": {"k": selected["k"], "home_advantage": selected["home_advantage"]},
        "incumbent_parameters": {"k": incumbent["k"], "home_advantage": incumbent["home_advantage"]},
        "development_brier_improvement": round(development_delta, 8),
        "holdout_brier_improvement": round(holdout_delta, 8),
        "recommendation": "candidate_warrants_further_validation" if meaningful else "retain_incumbent",
        "production_model": "workbook_2026_baseline",
        "promotion_authorized": False,
        "disclaimer": "Elo retrospective research is not the production workbook model or archived pregame evidence.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    decision = summarize(json.loads(args.study.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
