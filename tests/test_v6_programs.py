from copy import deepcopy
from pathlib import Path
import json
from cfb_analytics.v6_foundation import load_foundation
from cfb_analytics.v6_programs import program_context

ROOT=Path(__file__).resolve().parents[1]


def test_shared_real_program_context_preserves_missingness_and_periods():
    data=load_foundation(ROOT)
    results=json.loads((ROOT/'research/archive/verified/accepted-team-seasons.json').read_text())
    out=program_context(data,results)
    assert len(out['programs'])==139  # Includes Idaho's retained historical FBS seasons.
    assert sum(p['season']==2026 for p in out['programs'])==138
    texas=next(p for p in out['programs'] if p['team']=='Texas')
    assert texas['recent']['seasons']==[2023,2024,2025]
    assert texas['prior']['seasons']==[2019,2021,2022]
    assert texas['recent']['games']>0
    assert out['knowledge_as_of']==data['knowledge_as_of']
    # A missing source class cannot become a zero or an apparent recruiting change.
    altered=deepcopy(data)
    next(r for r in altered['team_seasons'] if r['team']=='Texas' and r['season']==2025)['recruiting']=None
    new=next(p for p in program_context(altered,results)['programs'] if p['team']=='Texas')
    assert new['blue_chip_share_change'] is None
    assert new['win_rate_change']==texas['win_rate_change']
    assert data==load_foundation(ROOT)
