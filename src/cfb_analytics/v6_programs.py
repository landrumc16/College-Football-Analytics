"""Shared descriptive drivers; no causal inference or changes to V5 grades."""
from math import fsum


def program_context(foundation, results):
    observed={(s['season'],t['team']):t for s in results['seasons'] for t in s['teams']}
    groups={}
    for row in foundation['team_seasons']:
        groups.setdefault(row['team'],[]).append(row)
    output=[]
    for team, rows in sorted(groups.items()):
        rows=sorted(rows,key=lambda r:r['season'])
        latest=rows[-1]
        completed=[r for r in rows if r['season_complete'] and r['season']!=2020 and (r['season'],team) in observed]
        recent, prior=completed[-3:],completed[-6:-3]
        def window(items):
            games=[observed[(r['season'],team)] for r in items]
            wins=sum(g['fbs_wins'] for g in games)
            n=sum(g['fbs_wins']+g['fbs_losses'] for g in games)
            recruiting=[r['recruiting'] for r in items if r['recruiting']]
            rated=sum(r['star_rated'] for r in recruiting)
            # Shares weight observed rated recruits, not equally weighted class means.
            blue=fsum(r['blue_chip_share']*r['star_rated'] for r in recruiting if r['blue_chip_share'] is not None)
            return {'seasons':[r['season'] for r in items],'games':n,'fbs_win_rate':wins/n if n else None,
                    'recruiting_seasons':len(recruiting),'rated_recruits':rated,
                    'blue_chip_share':blue/rated if rated else None}
        a,b=window(recent),window(prior)
        complete=len(recent)==len(prior)==3
        win_change=a['fbs_win_rate']-b['fbs_win_rate'] if complete and a['fbs_win_rate'] is not None and b['fbs_win_rate'] is not None else None
        recruiting_change=a['blue_chip_share']-b['blue_chip_share'] if complete and a['recruiting_seasons']==b['recruiting_seasons']==3 and a['blue_chip_share'] is not None and b['blue_chip_share'] is not None else None
        output.append({'team':team,'season':latest['season'],'recent':a,'prior':b,
                       'win_rate_change':win_change,'blue_chip_share_change':recruiting_change,
                       'recruiting':latest['recruiting'],'roster':latest['roster'],'coaching':latest['coaching'],
                       'source_ids':sorted({s for r in rows for s in r['source_ids']})})
    return {'schema_version':1,'status':'descriptive_source_verified_not_historical_pregame',
            'knowledge_as_of':foundation['knowledge_as_of'],'coverage':foundation['coverage'],
            'limitations':foundation['limitations'],'programs':output}
