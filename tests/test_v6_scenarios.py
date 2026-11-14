from pathlib import Path
import json
import pytest
from cfb_analytics.v6_scenarios import scenario_input,simulate_scenario
from cfb_analytics.cfp import simulate_cfp
ROOT=Path(__file__).resolve().parents[1]


def inputs():
    return scenario_input(json.loads((ROOT/'data/season-2026-report.json').read_text()),json.loads((ROOT/'data/cfbd-2026-games.json').read_text()))


def test_real_scenario_reset_and_probability_sanity():
    data=inputs();data['draws']=60
    baseline=simulate_scenario(data,now='2026-11-14T00:00:00Z')
    assert baseline==simulate_scenario(data,{},now='2026-11-14T00:00:00Z')
    assert abs(sum(t['cfp_field'] for t in baseline['teams'])-12)<.002
    assert abs(sum(t['national_title'] for t in baseline['teams'])-1)<.002
    for t in baseline['teams']:
        assert 0<=t['national_title']<=t['cfp_field']<=1
    g=next(g for g in data['games'] if g.get('start_date') and g['start_date']>'2026-11-15')
    changed=simulate_scenario(data,{str(g['game_id']):g['away']},now='2026-11-14T00:00:00Z')
    assert changed!=baseline
    assert simulate_scenario(data,{},now='2026-11-14T00:00:00Z')==baseline


@pytest.mark.parametrize('choice', [{'nonexistent':'Texas'},{'401862844':'Texas'}])
def test_invalid_scenario_rejected(choice):
    with pytest.raises(ValueError):simulate_scenario(inputs(),choice,now='2026-11-14T00:00:00Z')


def test_started_completed_and_duplicate_games_rejected():
    data=inputs();g=data['games'][-1];choice={str(g['game_id']):g['home']}
    with pytest.raises(ValueError,match='future'):simulate_scenario(data,choice,now='2027-01-01T00:00:00Z')
    g['completed']=True
    with pytest.raises(ValueError):simulate_scenario(data,choice,now='2026-11-14T00:00:00Z')
    g['completed']=False;data['games'].append(g)
    with pytest.raises(ValueError,match='unique'):simulate_scenario(data,choice,now='2026-11-14T00:00:00Z')


def test_default_incumbent_random_stream_unchanged():
    data=inputs()
    kw=dict(simulations=30,seed=2026,scale=data['scale'],home_edge=data['home_edge'],fcs_rating=data['fcs_rating'])
    assert simulate_cfp(data['teams'],data['games'],**kw)==simulate_cfp(data['teams'],data['games'],winner_overrides={},**kw)


def test_incumbent_default_matches_the_retained_10000_draw_production_report():
    report=json.loads((ROOT/'data/season-2026-report.json').read_text())
    data=inputs()
    assert simulate_cfp(data['teams'],data['games'],scale=data['scale'],home_edge=data['home_edge'],fcs_rating=data['fcs_rating'])==report['cfp']
