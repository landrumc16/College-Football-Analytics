"""Publish small static research/context packets without touching V5 data or models."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from cfb_analytics.v6_foundation import load_foundation
from cfb_analytics.v6_programs import program_context
from cfb_analytics.v6_scenarios import scenario_input

ROOT=Path(__file__).resolve().parents[1]


def publications():
    foundation=load_foundation(ROOT)
    context=program_context(foundation,json.loads((ROOT/'research/archive/verified/accepted-team-seasons.json').read_bytes()))
    registry=json.loads((ROOT/'research/v6/sources.json').read_bytes())
    context['sources']=[{k:s[k] for k in ['id','url','sha256']} for s in registry['sources']]
    context['foundation_sha256']=hashlib.sha256((ROOT/'research/v6/foundation.json.gz').read_bytes()).hexdigest()
    research=json.loads((ROOT/'research/v6/prediction-research.json').read_bytes())
    report=(ROOT/'data/season-2026-report.json').read_bytes()
    scenario=scenario_input(json.loads(report),json.loads((ROOT/'data/cfbd-2026-games.json').read_bytes()))
    scenario['report_sha256']=hashlib.sha256(report).hexdigest()
    return {'v6-program-context.json':context,'v6-prediction-research.json':research,'v6-scenario-input.json':scenario}


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    for name,value in publications().items():
        data=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
        path=ROOT/'web/public'/name
        if args.check:
            if path.read_bytes()!=data:raise ValueError('Product export differs: '+name)
        else:path.write_bytes(data)


if __name__=='__main__':main()
