"""Statistical/temporal guards on synthetic fixtures; never production forecasts."""
from copy import deepcopy
import pytest
from cfb_analytics.v6_prediction import (fit_logistic,predict,chronological_fold,
    program_features,matchup_features,freeze_prospective)

CONFIG={'epochs':150,'learning_rate':.15,'l2':.02,'probability_clip':1e-6}


def history(team='Fixture A'):
    return [{'season':year,'team':team,'fbs_wins':wins,'fbs_losses':10-wins}
            for year,wins in [(2018,3),(2019,5),(2020,10),(2021,7)]]


def test_features_exclude_current_future_and_disrupted_season():
    rows=history()
    x=program_features(rows,'Fixture A',2022)
    assert x[0]==.7 and x[1]==.5 and x[3]==10
    assert program_features(rows+[{'season':2022,'team':'Fixture A','fbs_wins':10,'fbs_losses':0}], 'Fixture A',2022)==x
    assert program_features(rows,'Unknown',2022) is None
    assert matchup_features(rows+history('Fixture B'),'Fixture A','Fixture B',2022,True)==[0,0,0,0,0]


def test_chronological_split_and_duplicates():
    rows=[{'season':year,'game_id':str(year)} for year in [2018,2019,2020,2021,2022,2023]]
    train,test=chronological_fold(rows,2022)
    assert [r['season'] for r in train]==[2018,2019,2021]
    assert [r['season'] for r in test]==[2022]
    with pytest.raises(ValueError):chronological_fold(rows+[rows[0]],2022)


def test_fit_is_deterministic_and_scales_training_only():
    xs=[[-2,1],[-1,1],[1,1],[2,1]];ys=[0,0,1,1]
    model=fit_logistic(xs,ys,CONFIG)
    assert model==fit_logistic(xs,ys,CONFIG)
    assert model['means']==[0,1] and model['scales'][1]==1
    assert predict(model,[-2,1])<.5<predict(model,[2,1])
    frozen=deepcopy(model);predict(model,[1000,1]);assert model==frozen
    with pytest.raises(ValueError):fit_logistic([[float('nan')]], [1],CONFIG)
    with pytest.raises(ValueError):predict(model,[1])


def test_prospective_requires_real_future_kickoff_and_matching_game():
    rows=history()+history('Fixture B');model=fit_logistic([[0,0,0,0,1],[1,1,.1,1,0]],[0,1],CONFIG)
    report={'predictions':[{'game_id':1,'home':'Fixture A','away':'Fixture B','home_win_probability':.6}]}
    game={'game_id':1,'home':'Fixture A','away':'Fixture B','season':2022,'week':1,'completed':False,'start_date':'2022-09-02T00:00:00Z','neutral_site':False}
    result=freeze_prospective(model,rows,report,[game],'2022-09-01T00:00:00Z','fixture-model')
    assert len(result['predictions'])==1 and result['model_status']=='experimental_not_promoted'
    assert not freeze_prospective(model,rows,report,[game],game['start_date'],'fixture')['predictions']
    assert not freeze_prospective(model,rows,report,[{**game,'start_date':None}],'2022-09-01T00:00:00Z','fixture')['predictions']
    assert not freeze_prospective(model,rows,report,[{**game,'away':'Wrong identity'}],'2022-09-01T00:00:00Z','fixture')['predictions']
    with pytest.raises(ValueError):freeze_prospective(model,rows,report,[game],'2022-09-01','fixture')


def test_independent_prospective_publication_receipt_and_model_hash():
    import hashlib,json
    from pathlib import Path
    from cfb_analytics.historical import utc_instant
    root=Path(__file__).resolve().parents[1]
    receipt=json.loads((root/'research/v6/experimental-publication.json').read_bytes())
    blob=(root/receipt['predictions_file']).read_bytes()
    assert hashlib.sha256(blob).hexdigest()==receipt['predictions_sha256']
    frozen=json.loads(blob)
    assert len(frozen['predictions'])==receipt['games']==178
    assert len({r['game_id'] for r in frozen['predictions']})==178
    published=utc_instant(receipt['publication_at'])
    for row in frozen['predictions']:
        assert utc_instant(row['issued_at'])<=published<utc_instant(row['kickoff_at'])
        assert 0<=row['incumbent_probability']<=1 and 0<=row['challenger_probability']<=1
    # Exact model bytes from the independently published run remain separately retained.
    assert hashlib.sha256((root/'research/v6/experimental-model-2026-11-14.json').read_bytes()).hexdigest()==frozen['predictions'][0]['model_input_hash']
