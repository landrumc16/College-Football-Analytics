import json
from pathlib import Path
from scripts.v9_accountability import retain, evaluate


def fixture():
    p={'game_id':1,'home':'A','away':'B','home_win_probability':.8,'home_margin':7}
    report={'season':2026,'generated_at':'2026-11-24T02:00:00Z','retrieved_at':'2026-11-24T01:00:00Z','model_metadata':{'model_id':'unchanged'},'predictions':[p]}
    dual={'generated_at':report['generated_at'],'data_retrieved_at':report['retrieved_at'],'games':[{**p,'standard':p,'momentum':p}]}
    snapshot={'retrieved_at':'2026-12-02T01:00:00Z','games':[{'game_id':1,'home':'A','away':'B','completed':False,'start_date':'2026-12-01T01:00:00Z','home_score':24,'away_score':17}]}
    return report,dual,snapshot


def rows(archive):
    return [json.loads(p.read_text()) for p in archive.glob('*.json')]


def test_first_retention_is_immutable_and_cannot_backfill(tmp_path):
    report,dual,snapshot=fixture()
    assert retain(tmp_path,report,dual,snapshot,now='2026-11-25T01:00:00Z',receipts={})==3
    before={p.name:p.read_bytes() for p in tmp_path.glob('*.json')}
    report['predictions'][0]['home_win_probability']=.1
    assert retain(tmp_path,report,dual,snapshot,now='2026-11-26T01:00:00Z',receipts={})==0
    assert {p.name:p.read_bytes() for p in tmp_path.glob('*.json')}==before
    assert retain(tmp_path/'late',report,dual,snapshot,now='2026-12-02T01:00:00Z',receipts={})==0


def test_same_game_scores_calibration_and_no_replay(tmp_path):
    report,dual,snapshot=fixture()
    retain(tmp_path,report,dual,snapshot,now='2026-11-25T01:00:00Z',receipts={})
    assert evaluate({},rows(tmp_path),snapshot,{'A','B'})['models']['official'] is None
    snapshot['games'][0]['completed']=True
    out=evaluate({},rows(tmp_path),snapshot,{'A','B'})
    assert out['common_games']==1
    for model in out['models'].values():
        assert model['games']==1 and abs(model['brier']-.04)<1e-10
        assert sum(b['games'] for b in model['calibration'])==1
        assert all(b['mean_predicted'] is None for b in model['calibration'] if b['games']==0)
    out=evaluate({},[r for r in rows(tmp_path) if r['model_id']=='official'],snapshot,{'A','B'})
    assert out['common_games']==0 and out['models']['standard'] is None


def test_late_retention_legacy_and_identity_are_excluded(tmp_path):
    report,dual,snapshot=fixture()
    retain(tmp_path,report,dual,snapshot,now='2026-11-25T01:00:00Z',receipts={})
    retained=rows(tmp_path)
    for row in retained:row['retained_at']='2026-12-01T01:00:00Z'
    snapshot['games'][0]['completed']=True
    out=evaluate({'1':{'source':'retrospective'}},retained,snapshot,{'A','B'})
    assert all(v is None for v in out['models'].values())
    assert out['exclusions']['legacy_without_complete_pregame_evidence']==1
    for row in retained:row['home']='Wrong identity'
    assert evaluate({},retained,snapshot,{'A','B'})['common_games']==0


def test_real_committed_retention_has_no_post_kickoff_rows():
    from cfb_analytics.forecast_ledger import aware_utc
    archive=Path('docs/evidence/v9/pregame')
    assert list(archive.glob('*.json'))
    for row in rows(archive):
        assert aware_utc(row['source_retrieved_at'])<=aware_utc(row['prediction_time'])<=aware_utc(row['retained_at'])<aware_utc(row['kickoff_time'])
        assert row['source']=='first_retained_before_kickoff'


def test_first_bundle_checksums_remain_immutable():
    import hashlib
    receipt=json.loads(Path('docs/evidence/v9/pregame-receipt.json').read_text())
    for name,digest in receipt['files'].items():
        assert hashlib.sha256((Path('docs/evidence/v9/pregame')/name).read_bytes()).hexdigest()==digest


def test_replay_cannot_claim_retention_status(tmp_path):
    report,dual,snapshot=fixture()
    retain(tmp_path,report,dual,snapshot,now='2026-11-25T01:00:00Z',receipts={})
    forged=rows(tmp_path)
    for row in forged:row['source']='retrospective_replay'
    snapshot['games'][0]['completed']=True
    result=evaluate({},forged,snapshot,{'A','B'})
    assert result['eligible_completed_games']==1
    assert all(value is None for value in result['models'].values())
    assert result['exclusions']['invalid_retained_archive_shape']==3
