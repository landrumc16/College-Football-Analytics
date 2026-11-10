"""Prepare reviewable trajectory measurements from the existing FBS schedule artifact.

This command deliberately never marks evidence independently reviewed.
Its output can be joined with reviewed poll and current-strength inputs
before invoking v5_program_report_card_cli.
"""
import argparse
import json
from pathlib import Path
from .v5_program_trajectory import trajectory_measurements

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--records",type=Path,required=True)
    p.add_argument("--coverage",type=Path,required=True)
    p.add_argument("--latest-completed-season",type=int,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    records=json.loads(a.records.read_text(encoding="utf-8"))
    coverage=json.loads(a.coverage.read_text(encoding="utf-8"))
    years=range(a.latest_completed_season-9,a.latest_completed_season+1)
    sources=coverage.get("seasons",{})
    if any(not sources.get(str(y),{}).get("source_sha256") or
           not sources[str(y)].get("source_url","").startswith("https://") for y in years if y!=2020):
        p.error("Incomplete historical source coverage; refusing export")
    source=coverage.get("source")
    if not isinstance(source,str) or not source.startswith("https://"):
        p.error("Invalid source")
    result=trajectory_measurements(records,latest_completed_season=a.latest_completed_season,source=source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({"status":"research_only_source_review_required",
        "latest_completed_season":a.latest_completed_season,
        "coverage":{str(y):sources[str(y)] for y in years if y!=2020},
        "trajectory":result},indent=2,sort_keys=True)+"\n",encoding="utf-8")

if __name__=="__main__":
    main()
