"""Static-host scenario adapter over the incumbent CFP simulation contract."""
from .cfp import simulate_cfp
from .historical import utc_instant

DRAWS=2000
SEED=2026


class ScenarioRandom:
    """Small identical unsigned-32 LCG for browser/Python parity; not model RNG."""
    def __init__(self,seed=SEED):self.state=seed
    def random(self):
        self.state=(1664525*self.state+1013904223)&0xffffffff
        return self.state/4294967296


def scenario_input(report,snapshot):
    standings={t['team']:t for rows in report['conference_standings'].values() for t in rows}
    teams={r['team']:{'conference':standings[r['team']]['conference'],'rating':r['rating'],
                      'wins':r['wins'],'conference_wins':standings[r['team']]['conference_wins']}
           for r in report['rankings']}
    from scripts.reconcile_v5_historical_sources import canonical
    source={str(g['game_id']):{**g,'home':canonical(g['home']),'away':canonical(g['away'])} for g in snapshot['games']}
    games=[]
    for game in report['schedule']:
        if game['completed']:continue
        original=source.get(str(game['game_id']))
        if not original or (original['home'],original['away']) != (game['home'],game['away']):
            raise ValueError('Schedule identity differs from source')
        games.append({**game,'start_date':original.get('start_date')})
    metadata=report['model_metadata']
    return {'schema_version':1,'season':report['season'],'retrieved_at':report.get('retrieved_at'),
            'teams':teams,'games':games,'scale':metadata['prediction_scale'],
            'home_edge':metadata['home_field_advantage'],'fcs_rating':-26.0,'draws':DRAWS,'seed':SEED}


def simulate_scenario(data,overrides=None,*,now):
    overrides=overrides or {}
    instant=utc_instant(now)
    if instant is None:raise ValueError('Scenario clock requires timezone')
    games={str(g['game_id']):g for g in data['games']}
    for game_id,winner in overrides.items():
        g=games.get(str(game_id))
        if not g or g['completed'] or winner not in (g['home'],g['away']):raise ValueError('Invalid scenario choice')
        kickoff=utc_instant(g.get('start_date'))
        if kickoff is None or kickoff<=instant:raise ValueError('Only scheduled future games can be overridden')
    return simulate_cfp(data['teams'],data['games'],simulations=data['draws'],seed=data['seed'],
                        scale=data['scale'],home_edge=data['home_edge'],fcs_rating=data['fcs_rating'],
                        winner_overrides=overrides,random_source=ScenarioRandom(data['seed']))
