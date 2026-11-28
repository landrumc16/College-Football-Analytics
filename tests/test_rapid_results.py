import copy
import json
import pytest
from cfb_analytics.rapid_results import transition, public_snapshot, save_state, export_confirmed

SCHEDULE=[{'game_id':1,'home':'Texas Tech','away':'TCU','completed':False}]
SOURCES={'https://licensed.example/finals':'licensed','https://api.collegefootballdata.com/games':'cfbd'}
def row(score=48):
 return dict(kind='game_final',game_id=1,home='Texas Tech',away='TCU',home_score=score,away_score=27,status='final',source='https://licensed.example/finals',published_at='2026-11-26T20:00:00Z',observed_at='2026-11-26T20:01:00Z',basic_stats={'home':{'total_yards':400}})
def verified(score=48):
 r=row(score);r.update(source='https://api.collegefootballdata.com/games',observed_at='2026-11-27T20:00:00Z');return r

def test_entire_lifecycle_and_immutable_corrections(tmp_path):
 state=transition(None,row(),SCHEDULE,SOURCES)
 assert state['events'][0]['status']=='provisional'
 assert not state['events'][0]['model_ingestion_allowed']
 assert public_snapshot(state,SCHEDULE)['records']['Texas Tech']==dict(wins=1,losses=0,provisional_games=1)
 path=tmp_path/'state.json';save_state(path,state,expected_revision=0)
 confirmed=transition(state,verified(),SCHEDULE,SOURCES,authoritative=True)
 save_state(path,confirmed,expected_revision=1);export_confirmed(confirmed,tmp_path/'archive')
 original={p.name:p.read_bytes() for p in (tmp_path/'archive').iterdir()}
 corrected=verified(20);corrected['observed_at']='2026-11-28T00:00:00Z'
 final=transition(confirmed,corrected,SCHEDULE,SOURCES,authoritative=True)
 assert final['events'][0]['status']=='corrected'
 assert public_snapshot(final,SCHEDULE)['records']['Texas Tech']['losses']==1
 export_confirmed(final,tmp_path/'archive')
 assert all((tmp_path/'archive'/n).read_bytes()==b for n,b in original.items())
 assert len(list((tmp_path/'archive').iterdir()))==2
 assert transition(final,corrected,SCHEDULE,SOURCES,authoritative=True)==final
 assert SCHEDULE[0]['completed'] is False

def test_admission_identity_stats_and_upstream():
 for patch in ({'source':'https://unauthorized.example/'},{'home':'Unknown'},{'home_score':27},{'basic_stats':{'home':{'total_yards':-1}}}):
  r=row();r.update(patch)
  with pytest.raises(ValueError):transition(None,r,SCHEDULE,SOURCES)
 with pytest.raises(ValueError,match='requires CFBD'):transition(None,row(),SCHEDULE,SOURCES,authoritative=True)

def test_concurrent_and_archive_rewrite_fail_closed(tmp_path):
 s=transition(None,row(),SCHEDULE,SOURCES);p=tmp_path/'state';save_state(p,s,expected_revision=0)
 with pytest.raises(ValueError,match='Concurrent'):save_state(p,s,expected_revision=0)
 s['history']=[]
 with pytest.raises(ValueError,match='history rewrite'):save_state(p,s,expected_revision=1)

def test_verified_score_not_displaced_by_secondary():
 s=transition(None,verified(),SCHEDULE,SOURCES,authoritative=True)
 r=row(20);r['observed_at']='2026-11-28T00:00:00Z'
 s=transition(s,r,SCHEDULE,SOURCES)
 assert s['events'][0]['status']=='disputed'
 assert s['events'][0]['home_score']==48

def test_cli_restart_reconcile_and_replay(tmp_path, monkeypatch):
 from cfb_analytics.rapid_results_cli import main
 import sys
 report={'retrieved_at':'2026-11-27T20:00:00Z','schedule':SCHEDULE}
 for name,value in [('schedule',report),('sources',{'enabled':True,'sources':SOURCES}),('inbox',{'batch_id':'fixture-1','observations':[{'observation':row()}]}),('cfbd',{'retrieved_at':'2026-11-27T20:00:00Z','games':[dict(SCHEDULE[0],completed=True,home_score=20,away_score=27)]})]:
  (tmp_path/name).write_text(json.dumps(value))
 args=['rapid']
 for k in ('inbox','schedule','sources','state','output','archive'):args+=['--'+k,str(tmp_path/k)]
 monkeypatch.setattr(sys,'argv',args);main()
 public=json.loads((tmp_path/'output').read_text())
 assert public['records']['Texas Tech']['wins']==1
 assert public['events'][0]['statistics_pending']
 monkeypatch.setattr(sys,'argv',args+['--cfbd-snapshot',str(tmp_path/'cfbd'),'--confirmed-games',str(tmp_path/'confirmed')]);main()
 public=json.loads((tmp_path/'output').read_text())
 assert public['records']['Texas Tech']['losses']==1
 assert public['events'][0]['status']=='corrected'
 assert json.loads((tmp_path/'confirmed').read_text())[0]['home_score']==20
 before=(tmp_path/'state').read_bytes();main()
 assert (tmp_path/'state').read_bytes()==before
 assert json.loads((tmp_path/'schedule').read_text())==report
 assert len(list((tmp_path/'archive').glob('*.json')))==1

def test_cli_processed_batch_survives_corrected_schedule_and_stale_cfbd(tmp_path, monkeypatch):
 from cfb_analytics.rapid_results_cli import main
 import sys
 for name,value in [('schedule',{'schedule':SCHEDULE}),('sources',{'enabled':True,'sources':SOURCES}),('inbox',{'batch_id':'stable','observations':[{'observation':row()}]})]:
  (tmp_path/name).write_text(json.dumps(value))
 args=['rapid']
 for k in ('inbox','schedule','sources','state','output','archive'):args+=['--'+k,str(tmp_path/k)]
 monkeypatch.setattr(sys,'argv',args);main()
 cfbd={'retrieved_at':'2026-11-26T19:00:00Z','games':[dict(SCHEDULE[0],completed=True,home_score=20,away_score=27)]}
 (tmp_path/'cfbd').write_text(json.dumps(cfbd))
 monkeypatch.setattr(sys,'argv',args+['--cfbd-snapshot',str(tmp_path/'cfbd')]);main()
 assert json.loads((tmp_path/'output').read_text())['events'][0]['status']=='provisional'
 cfbd['retrieved_at']='2026-11-27T20:00:00Z';(tmp_path/'cfbd').write_text(json.dumps(cfbd));main()
 (tmp_path/'schedule').write_text(json.dumps({'schedule':cfbd['games']}));main()
 event=json.loads((tmp_path/'output').read_text())['events'][0]
 assert event['home_score']==20
 assert event['basic_stats']==row()['basic_stats']
 assert event['statistics_verified'] is False
 assert event['statistics_source']==row()['source']
 inbox=json.loads((tmp_path/'inbox').read_text());inbox['observations'][0]['observation']['home_score']=49
 (tmp_path/'inbox').write_text(json.dumps(inbox))
 with pytest.raises(ValueError,match='different content'):main()

def test_cfbd_known_aliases(tmp_path, monkeypatch):
 from cfb_analytics.rapid_results_cli import main
 import sys
 schedule=[dict(SCHEDULE[0],home='Miami (FL)')];r=row();r['home']='Miami (FL)'
 for name,value in [('schedule',schedule),('sources',{'enabled':True,'sources':SOURCES}),('inbox',{'batch_id':'alias','observations':[{'observation':r}]}),('cfbd',{'retrieved_at':'2026-11-27T20:00:00Z','games':[dict(schedule[0],home='Miami',completed=True,home_score=48,away_score=27)]})]:
  (tmp_path/name).write_text(json.dumps(value))
 args=['rapid']
 for k in ('inbox','schedule','sources','state','output','archive','cfbd-snapshot'):args+=['--'+k,str(tmp_path/('cfbd' if k=='cfbd-snapshot' else k))]
 monkeypatch.setattr(sys,'argv',args);main()
 assert json.loads((tmp_path/'output').read_text())['events'][0]['status']=='confirmed'
