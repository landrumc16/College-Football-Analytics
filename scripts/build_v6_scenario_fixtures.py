"""Retain Python reference fixtures for the browser port, no generated football facts."""
import json
from pathlib import Path
from cfb_analytics.v6_scenarios import scenario_input,simulate_scenario
ROOT=Path(__file__).resolve().parents[1]

def build():
    data=scenario_input(json.loads((ROOT/'data/season-2026-report.json').read_text()),json.loads((ROOT/'data/cfbd-2026-games.json').read_text()))
    now='2026-11-14T00:00:00Z'
    g=data['games'][-1]
    cases=[]
    for overrides in [{},{str(g['game_id']):g['home']},{str(g['game_id']):g['away']}]:
        out=simulate_scenario(data,overrides,now=now)
        cases.append({'overrides':overrides,'teams':[{k:t[k] for k in ['team','conference_title','cfp_field','national_title']} for t in sorted(out['teams'],key=lambda t:t['team'])]})
    return {'input':data,'now':now,'cases':cases}

if __name__=='__main__':
    (ROOT/'research/v6/scenario-python-fixtures.json').write_text(json.dumps(build(),sort_keys=True,separators=(',',':'))+'\n')
