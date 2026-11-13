"""Publish source-attested FBS report cards without manufacturing missing data.

Input JSON: {"as_of":"YYYY-MM-DD","eligible_fbs":["..."],
"measurements":{"Team":{"hype":{"value":1.2,"source":"...","verified":true},
"trajectory":{...},"strength":{...}}}}.
"""
import argparse
import json
from pathlib import Path
from .v5_program_report_card import build_report_cards

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=Path("web/public/v5-program-report-cards.json"))
    parser.add_argument("--minimum-coverage",type=float,default=0.8)
    args=parser.parse_args()
    data=json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(data,dict) or not {"as_of","eligible_fbs","measurements"} <= data.keys():
        parser.error("Missing required source-attested input fields")
    roster=data["eligible_fbs"]
    if not isinstance(roster,list) or len(roster)<120:
        parser.error("Refusing cohort-only grades: national FBS peer roster required")
    if not data.get("eligible_fbs_reviewed") or not isinstance(data.get("eligible_fbs_source"),str) or not data["eligible_fbs_source"].startswith("https://"):
        parser.error("Missing independently reviewed eligible-FBS roster provenance")
    result=build_report_cards(data["measurements"],eligible_fbs=roster,as_of=data["as_of"],minimum_coverage=args.minimum_coverage)
    result["eligible_fbs_source"]=data["eligible_fbs_source"]
    if not all(c["national_grades_available"] for c in result["coverage"].values()):
        parser.error("Insufficient verified national FBS coverage: refusing publication")
    if not any(p["overall_grade"] is not None for p in result["programs"]):
        parser.error("No complete verified report card: refusing publication")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
