"""Minimal isolated challenger. Chronological replay is never an archived forecast.

No production module imports this code. New recruiting/roster/coaching domains
are excluded from historical fitting because their cutoff availability is unproven.
"""
from __future__ import annotations
from math import exp, isfinite, log, sqrt, fsum
from .historical import utc_instant


def probability(score):
    if score >= 0:
        z = exp(-min(score, 700))
        return 1 / (1 + z)
    z = exp(max(score, -700))
    return z / (1 + z)


def fit_logistic(xs, ys, config):
    if not xs or len(xs) != len(ys) or not xs[0]:
        raise ValueError('Need paired nonempty training observations')
    width, count = len(xs[0]), len(xs)
    if any(len(row) != width or any(type(x) not in (int,float) or not isfinite(x) for x in row) for row in xs):
        raise ValueError('Invalid training feature matrix')
    if any(y not in (0,1) for y in ys):
        raise ValueError('Training labels must be binary')
    means = [fsum(row[i] for row in xs)/count for i in range(width)]
    scales = [sqrt(fsum((row[i]-means[i])**2 for row in xs)/count) or 1.0 for i in range(width)]
    values = [[(x-means[i])/scales[i] for i,x in enumerate(row)] for row in xs]
    prior = (sum(ys)+1)/(count+2)
    intercept, weights = log(prior/(1-prior)), [0.0]*width
    for _ in range(config['epochs']):
        gradients, bias = [0.0]*width, 0.0
        for row,y in zip(values,ys):
            error = probability(intercept + fsum(w*x for w,x in zip(weights,row))) - y
            bias += error
            for i,x in enumerate(row):gradients[i] += error*x
        intercept -= config['learning_rate'] * bias/count
        weights = [w-config['learning_rate']*(gradients[i]/count+config['l2']*w) for i,w in enumerate(weights)]
    return {'means':means,'scales':scales,'weights':weights,'intercept':intercept,
            'training_games':count,'config':dict(config)}


def predict(model, row):
    if len(row) != len(model['weights']) or any(not isfinite(x) for x in row):
        raise ValueError('Invalid prediction features')
    value = model['intercept'] + fsum(w*(x-m)/s for w,x,m,s in zip(model['weights'],row,model['means'],model['scales']))
    clip = model['config']['probability_clip']
    return min(1-clip,max(clip,probability(value)))


def program_features(records, team, season):
    # Completed non-2020 seasons only; never current-season roster or final rankings.
    prior = sorted([r for r in records if r['team']==team and r['season']<season and r['season']!=2020
                    and r['fbs_wins']+r['fbs_losses']>0],key=lambda r:r['season'],reverse=True)[:3]
    if len(prior)<2:return None
    n = sum(r['fbs_wins']+r['fbs_losses'] for r in prior)
    years = [r['season'] for r in prior]
    rates = [r['fbs_wins']/(r['fbs_wins']+r['fbs_losses']) for r in prior]
    ym, rm = sum(years)/len(years), fsum(rates)/len(rates)
    slope = fsum((y-ym)*(p-rm) for y,p in zip(years,rates))/fsum((y-ym)**2 for y in years)
    return [rates[0],sum(r['fbs_wins'] for r in prior)/n,slope,prior[0]['fbs_wins']+prior[0]['fbs_losses']]


def matchup_features(records, home, away, season, neutral):
    h, a = program_features(records,home,season), program_features(records,away,season)
    if h is None or a is None:return None
    return [x-y for x,y in zip(h,a)] + [0.0 if neutral else 1.0]


def chronological_fold(rows, season):
    train = [r for r in rows if r['season'] < season and r['season'] != 2020]
    test = [r for r in rows if r['season'] == season]
    if not train or not test or any(r['season'] >= season for r in train):
        raise ValueError('Invalid chronological split')
    if len({r['game_id'] for r in train+test}) != len(train+test):
        raise ValueError('Duplicate or overlapping game identity')
    return train,test


def freeze_prospective(model, records, report, schedule, issued_at, model_input_hash):
    instant = utc_instant(issued_at)
    if instant is None:raise ValueError('Issuance requires timezone')
    predictions = {str(r['game_id']):r for r in report['predictions']}
    output = []
    for game in schedule:
        kickoff = utc_instant(game.get('start_date'))
        if game['completed'] or kickoff is None or kickoff <= instant:continue
        original = predictions.get(str(game['game_id']))
        if not original or (original['home'],original['away']) != (game['home'],game['away']):continue
        x = matchup_features(records,game['home'],game['away'],game['season'],game['neutral_site'])
        if x is None:continue
        output.append({'game_id':str(game['game_id']),'season':game['season'],'week':game['week'],
                       'home':game['home'],'away':game['away'],'kickoff_at':game['start_date'],
                       'issued_at':issued_at,'challenger_probability':predict(model,x),
                       'incumbent_probability':original['home_win_probability'],'model_input_hash':model_input_hash})
    return {'schema_version':1,'model_status':'experimental_not_promoted','issued_at':issued_at,
            'publication_status':'requires_independent_pre_kickoff_publication_receipt',
            'predictions':sorted(output,key=lambda r:(r['kickoff_at'],r['game_id']))}
