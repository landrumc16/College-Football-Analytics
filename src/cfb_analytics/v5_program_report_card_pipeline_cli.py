"""Build reviewed V5 report cards from existing historical research artifacts.

Research inputs are not automatically verified. Review booleans must be
explicit, and the full eligible-FBS roster must be independently supplied.
"""
import argparse
import json
from pathlib import Path
from .v5_program_report_card_pipeline import assemble_report_cards


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--poll-history",type=Path,required=True)
    p.add_argument("--team-season-records",type=Path,required=True)
    p.add_argument("--current-v4-rankings",type=Path,required=True)
    p.add_argument("--eligible-fbs",type=Path,required=True)
    p.add_argument("--source-review",type=Path,required=True)
    p.add_argument("--as-of",required=True)
    p.add_argument("--latest-completed-season",type=int,required=True)
    p.add_argument("--output",type=Path,default=Path("web/public/v5-program-report-cards.json"))
    args=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    review=read(args.source_review)
    required=("poll_reviewed","results_reviewed","strength_reviewed",
              "strength_source","results_source","eligible_fbs_source",
              "eligible_fbs_reviewed")
    if any(k not in review for k in required):
        p.error("Incomplete independent source-review attestation")
    if any(type(review[k]) is not bool for k in ("poll_reviewed","results_reviewed",
                                                  "strength_reviewed","eligible_fbs_reviewed")):
        p.error("Source review flags must be booleans")
    if not review["eligible_fbs_reviewed"] or not str(review["eligible_fbs_source"]).startswith("https://"):
        p.error("Verified national FBS peer roster required")
    if not any(review[k] for k in ("poll_reviewed","results_reviewed","strength_reviewed")):
        p.error("At least one category requires independent source review")
    eligible=read(args.eligible_fbs)
    if not isinstance(eligible,list) or len(eligible)<120:
        p.error("Refusing cohort-only publication; expected national FBS roster")
    current=read(args.current_v4_rankings)
    if isinstance(current,dict):
        current=current.get("teams")
    result=assemble_report_cards(
        poll_rows=read(args.poll_history),
        season_records=read(args.team_season_records),
        current_rankings=current,eligible_fbs=eligible,
        as_of=args.as_of,latest_completed_season=args.latest_completed_season,
        poll_reviewed=review["poll_reviewed"],
        results_reviewed=review["results_reviewed"],
        strength_reviewed=review["strength_reviewed"],
        strength_source=review["strength_source"],results_source=review["results_source"])
    if not any(v["national_grades_available"] for v in result["coverage"].values()):
        p.error("No reviewed category has sufficient national coverage")
    result["publication_status"] = ("complete" if all(
        v["national_grades_available"] for v in result["coverage"].values())
        else "partial_verified_categories_only")
    result["eligible_fbs_source"]=review["eligible_fbs_source"]
    result["source_review"]=dict(result["source_review"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
