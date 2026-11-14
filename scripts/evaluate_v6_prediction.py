"""Frozen four-fold exploratory replay plus separately verified published incumbent.

No historical source is relabelled pregame; no proxy result authorizes promotion.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from math import fsum
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from cfb_analytics.v6_foundation import load_foundation,require_historical_pregame_eligibility
from cfb_analytics.v6_prediction import fit_logistic,predict,matchup_features,chronological_fold,freeze_prospective
from cfb_analytics.v4_evaluation import evaluate_pairs,clustered_brier_interval
from scripts.verify_v5_pregame_archive import verify
from scripts.reconcile_v5_historical_sources import canonical

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'research/v6'


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())


def stable(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def rename_reference(value):
    if isinstance(value,dict):return {('reference' if k=='incumbent' else k):rename_reference(v) for k,v in value.items()}
    if isinstance(value,list):return [rename_reference(v) for v in value]
    return value


def features_and_games():
    seasons=read(ROOT/'research/archive/verified/accepted-team-seasons.json')['seasons']
    records=[{'season':s['season'],**r} for s in seasons for r in s['teams']]
    games=read(ROOT/'research/archive/verified/espn-games.json.gz')
    disputed={'401014983','401021686','401309645'}
    rows=[]; eligible=Counter(); excluded=Counter()
    for year,items in sorted(games.items()):
        year=int(year)
        if year==2020:continue
        for g in items:
            if not g['fbs_game'] or str(g['game_id']) in disputed:continue
            eligible[year]+=1
            home,away=canonical(g['home']),canonical(g['away'])
            x=matchup_features(records,home,away,year,g['neutral_site'])
            if x is None:excluded[year]+=1;continue
            rows.append({'season':year,'week':g['week'],'game_id':str(g['game_id']),
                         'home':home,'away':away,'features':x,'outcome':int(g['home_score']>g['away_score'])})
    return records,rows,eligible,excluded


def run():
    protocol=read(DEST/'evaluation-protocol.json')
    foundation=load_foundation(ROOT)
    try:require_historical_pregame_eligibility(foundation,'2022-09-01T00:00:00Z')
    except ValueError:historical_context_eligible=False
    else:raise ValueError('Unverified contextual inputs unexpectedly became eligible')
    records,rows,eligible,excluded=features_and_games()
    config=protocol['fitting']; references=protocol['reference_feature_indices']
    pairs=[];folds=[]
    conferences={(r['season'],r['team']):r['conference'] or 'Unavailable' for r in foundation['team_seasons']}
    for season in protocol['primary_heldout_seasons']:
        train,test=chronological_fold(rows,season)
        reference=fit_logistic([[r['features'][i] for i in references] for r in train],[r['outcome'] for r in train],config)
        challenger=fit_logistic([r['features'] for r in train],[r['outcome'] for r in train],config)
        for r in test:
            pairs.append({k:r[k] for k in ['season','week','game_id','outcome']}|{
                'home_conference':conferences.get((season,r['home']),'Unavailable'),
                'prediction_kind':'retrospective','incumbent_probability':predict(reference,[r['features'][i] for i in references]),
                'challenger_probability':predict(challenger,r['features'])})
        folds.append({'season':season,'training_seasons':sorted({r['season'] for r in train}),
                      'training_games':len(train),'paired_games':len(test),'eligible_games':eligible[season],
                      'feature_coverage':len(test)/eligible[season],'missing_history_games':excluded[season]})
    metrics=rename_reference(evaluate_pairs(pairs))
    ci=clustered_brier_interval(pairs,draws=protocol['promotion_gates']['bootstrap_draws'],seed=protocol['promotion_gates']['seed'])
    limits=protocol['promotion_gates']
    pooled=metrics['retrospective']
    by_season=metrics['retrospective_by_season']
    def calibration_error(bins):
        n=sum(b['games'] for b in bins)
        return fsum(b['games']*abs(b['mean_probability']-b['observed_win_rate']) for b in bins if b['games'])/n if n else None
    reference_ece=calibration_error(pooled['calibration']['reference'])
    challenger_ece=calibration_error(pooled['calibration']['challenger'])
    log_change=(pooled['challenger']['log_loss']-pooled['reference']['log_loss'])/pooled['reference']['log_loss']
    proxy_screen={'brier_reduction_at_least_5_percent':pooled['relative_brier_reduction']>=limits['relative_brier_improvement'],
                  'improved_in_at_least_three_folds':sum(v['relative_brier_reduction']>0 for v in by_season.values())>=limits['seasons_improved'],
                  'logloss_regression_at_most_2_percent':log_change<=limits['maximum_relative_logloss_regression'],
                  'clustered_interval_excludes_zero':ci['ci95_upper']<0,
                  'coverage_floor':all(f['feature_coverage']>=limits['minimum_common_game_coverage_per_season'] for f in folds),
                  'sample_size':len(pairs)>=limits['minimum_pooled_games'] and all(f['paired_games']>=limits['minimum_paired_games_per_season'] for f in folds),
                  'calibration':challenger_ece<=limits['maximum_weighted_calibration_error'] and challenger_ece-reference_ece<=limits['maximum_calibration_error_increase']}
    # This is a reference-proxy screen; never call its metrics incumbent evidence.
    metrics['reference_screen']={'criteria':proxy_screen,'all_pass':all(proxy_screen.values()),'reference_ece':reference_ece,'challenger_ece':challenger_ece,'promotion_authority':False}
    metrics['comparison_label']='prior-results reference proxy vs experimental challenger'
    metrics['clustered_challenger_minus_reference_interval']=ci
    metrics['by_home_conference']={c:rename_reference(evaluate_pairs([r for r in pairs if r['home_conference']==c]))['retrospective']
                                   for c in sorted({r['home_conference'] for r in pairs})}
    final=fit_logistic([r['features'] for r in rows if r['season']<=2025],[r['outcome'] for r in rows if r['season']<=2025],config)
    verified,_,authentic=verify()
    finals=read(ROOT/'research/archive/verified/pregame-evaluation-outcomes.json')
    schedules={str(g['game_id']):g for g in finals['schedule']}
    archived_pairs=[]
    for archived in verified:
        g=schedules[archived['game_id']]
        x=matchup_features(records,canonical(g['home']),canonical(g['away']),2026,g['neutral_site'])
        if x is None:continue
        archived_pairs.append({'season':2026,'week':g['week'],'game_id':archived['game_id'],
            'outcome':int(archived['home_won']),'prediction_kind':'retrospective',
            'incumbent_probability':archived['home_win_probability'],'challenger_probability':predict(final,x)})
    input_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [
        'research/v6/evaluation-protocol.json','research/v6/foundation.json.gz',
        'research/archive/verified/accepted-team-seasons.json','research/archive/verified/espn-games.json.gz',
        'research/archive/verified/verified-pregame-rows.json']}
    report={'schema_version':1,'model_status':'experimental_not_promoted','protocol':protocol,'input_hashes':input_hashes,
            'authentic_incumbent':authentic['models']['workbook_2026_baseline'],
            'authentic_scope':authentic['evaluation_scope'],'authentic_publication':authentic['forecast_publication'],
            'chronological_research':metrics,'folds':folds,
            'archived_cohort_replay':evaluate_pairs(archived_pairs),
            'archived_cohort_replay_label':'incumbent probabilities genuinely archived; challenger replayed later, not a historical live forecast',
            'feature_policy':{'historical_context_inputs_eligible':historical_context_eligible,
                              'excluded_families':['historical recruiting snapshots','roster biography/continuity snapshots','dominant-coach attribution snapshots'],
                              'used':'lagged completed non-2020 FBS results only; no held-out/current-season outcomes in features'},
            'promotion':{'eligible':False,'authorized':False,'incumbent_retained':True,
                         'gates':{'true_incumbent_four_season_comparison':False,'verified_original_historical_feature_cutoffs':False,
                                  'incumbent_brier_improvement':None,'incumbent_season_stability':None,'incumbent_logloss':None,
                                  'incumbent_clustered_interval':None,'incumbent_calibration_and_coverage':None},
                         'blockers':['Four true historical incumbent-paired seasons lack season-specific incumbent priors',
                                     'Historical original feature-publication timestamps are not independently established',
                                     'The four-season comparison is a reference proxy, not the incumbent promotion cohort'],
                         'decision':'retain_incumbent; continue isolated prospective research'},
            'limitations':['Chronological ordering alone does not prove historical publication cutoffs',
                           'No proxy/replay score is an authentic historical challenger prediction or production improvement',
                           'Only the retained 65-game incumbent cohort has independently verified publication evidence',
                           'Prospective experimental performance requires games to finish and independent publication/final-outcome checks']}
    export_pairs=[{**{k:v for k,v in r.items() if k!='incumbent_probability'},'reference_probability':r['incumbent_probability']} for r in pairs]
    return report,final,records,export_pairs


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=DEST)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--prospective-output',type=Path)
    args=parser.parse_args()
    report,model,records,pairs=run()
    args.output.mkdir(parents=True,exist_ok=True)
    outputs={'prediction-research.json':stable(report),'challenger-model.json':stable(model),
             'research-paired-predictions.json.gz':gzip.compress(stable(pairs),mtime=0)}
    for name,data in outputs.items():
        p=args.output/name
        if args.check:
            actual=p.read_bytes()
            if name.endswith('.gz'):actual,data=gzip.decompress(actual),gzip.decompress(data)
            if actual!=data:
                # Preserve diagnostics before failing; never accept a changed score silently.
                from tempfile import gettempdir
                (Path(gettempdir())/('v6-regenerated-'+name.removesuffix('.gz'))).write_bytes(data)
                def difference(a,b,path='$'):
                    if type(a)!=type(b):return path+': types differ'
                    if isinstance(a,dict):
                        if a.keys()!=b.keys():return path+': keys differ'
                        return next((d for k in a if (d:=difference(a[k],b[k],path+'.'+k))),None)
                    if isinstance(a,list):
                        if len(a)!=len(b):return path+': lengths differ'
                        return next((d for i,(x,y) in enumerate(zip(a,b)) if (d:=difference(x,y,path+f'[{i}]'))),None)
                    return f'{path}: retained={a!r}, replay={b!r}' if a!=b else None
                raise ValueError('Research replay differs: '+name+' '+str(difference(json.loads(actual),json.loads(data))))
        else:p.write_bytes(data)
    if args.prospective_output:
        report_now=read(ROOT/'data/season-2026-report.json');snapshot=read(ROOT/'data/cfbd-2026-games.json')
        issued=datetime.now(timezone.utc).isoformat()
        schedule=[{**g,'home':canonical(g['home']),'away':canonical(g['away'])} for g in snapshot['games']]
        prospective=freeze_prospective(model,records,report_now,schedule,issued,hashlib.sha256(stable(model)).hexdigest())
        prospective['input_hashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['data/season-2026-report.json','data/cfbd-2026-games.json','research/archive/verified/accepted-team-seasons.json']}
        args.prospective_output.write_bytes(stable(prospective))
    print(json.dumps({'folds':report['folds'],'authentic_games':report['authentic_incumbent']['games'],
                      'promotion':report['promotion']}))


if __name__=='__main__':main()
