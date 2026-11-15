"""Reliability experiment over the released engines; no model fitting or changes."""
from copy import deepcopy
from hashlib import sha256
import json,math,subprocess,time
from pathlib import Path
from cfb_analytics.v6_scenarios import simulate_scenario
from cfb_analytics.cfp import simulate_cfp
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'web/adversarial-evidence';OUT.mkdir(exist_ok=True,parents=True)
packet=json.loads((ROOT/'web/dist/v6-scenario-input.json').read_text())
report=json.loads((ROOT/'web/dist/season-report.json').read_text())
now='2026-11-14T00:00:00Z'
g=next(g for g in packet['games'] if g['home']=='Army' and g['start_date'] and g['start_date']>now)
choices=[{}, {str(g['game_id']):g['home']},{str(g['game_id']):g['away']}]
records=[];runs=[];start=time.monotonic()
def run(name,fn):
    try:records.append({'name':name,'status':'PASS','details':fn()})
    except Exception as e:records.append({'name':name,'status':'FAIL','error':str(e)})
def bounds(teams):
    for t in teams:
        for key in ('cfp_field','conference_title','national_title'):assert math.isfinite(t[key]) and 0<=t[key]<=1,(t,key)
        assert t['national_title']<=t['cfp_field']
    assert abs(sum(t['cfp_field'] for t in teams)-12)<.01
    assert abs(sum(t['national_title'] for t in teams)-1)<.01
    for conf in set(t['conference'] for t in report['rankings'] if 'conference' in t):pass
    for conf in {x['conference'] for x in packet['teams'].values()}-{'Independent'}:
        assert abs(sum(t['conference_title'] for t in teams if packet['teams'][t['team']]['conference']==conf)-1)<.01
    return True
for seed in [0,1,17,42,2026,65535,2147483647,4294967295]:
    for choice in choices:
        data={**packet,'seed':seed}
        def case(data=data,choice=choice):
            result=simulate_scenario(data,choice,now=now)
            bounds(result['teams'])
            assert result==simulate_scenario(data,choice,now=now),'Same seed/choices not reproducible'
            runs.append({'input':data,'overrides':choice,'now':now,'teams':[{k:t[k] for k in ['team','conference_title','cfp_field','national_title']} for t in sorted(result['teams'],key=lambda t:t['team'])]})
            return {'seed':data['seed'],'draws':data['draws'],'choice':choice,'teams':len(result['teams'])}
        run('python-2000-draw-'+str(seed)+'-'+str(len(choice))+'-'+str(next(iter(choice.values()),'baseline')),case)
# Existing browser adapter is transpiled, not reimplemented.
(ROOT/'web/adversarial-evidence/parity-inputs.json').write_text(json.dumps(runs))
js="""import ts from 'typescript';import{readFile,writeFile}from'node:fs/promises';import assert from'node:assert/strict';const source=await readFile('web/src/scenarios.ts','utf8');const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;const{simulate}=await import('data:text/javascript,'+encodeURIComponent(js));const runs=JSON.parse(await readFile('web/adversarial-evidence/parity-inputs.json','utf8'));const times=[];for(const r of runs){const a=simulate(r.input,r.overrides,r.now);assert.deepEqual(a.teams,r.teams);assert.deepEqual(simulate(r.input,r.overrides,r.now).teams,r.teams);times.push(a.milliseconds)}await writeFile('web/adversarial-evidence/browser-mc.json',JSON.stringify({cases:runs.length,pythonBrowserParity:'exact',repeat:'exact',minMs:Math.min(...times),maxMs:Math.max(...times)}));"""
(ROOT/'web/tests/adversarial-mc-generated.mjs').write_text(js)
def browser_parity():
    subprocess.run(['node','web/tests/adversarial-mc-generated.mjs'],cwd=ROOT,check=True)
    return json.loads((OUT/'browser-mc.json').read_text())
run('python-browser-multi-seed-exact-parity',browser_parity)
def stability():
    bases=[r for r in runs if not r['overrides']];assert len(bases)==8
    by={}
    for r in bases:
        for t in r['teams']:
            for key in ['cfp_field','conference_title','national_title']:by.setdefault((t['team'],key),[]).append(t[key])
    max_dev=max(abs(x-sum(xs)/len(xs)) for xs in by.values() for x in xs)
    limit=6*math.sqrt(.25/packet['draws'])+.0001
    assert max_dev<=limit,(max_dev,limit)
    return {'seeds':8,'drawsPerSeed':2000,'maxDeviationFromSeedMean':max_dev,'conservativeSixStandardErrorLimit':limit,'scope':'Monte Carlo numeric stability, not forecast accuracy'}
run('multi-seed-stability',stability)
def production():
    args=dict(scale=packet['scale'],home_edge=packet['home_edge'],fcs_rating=packet['fcs_rating'])
    a=simulate_cfp(packet['teams'],packet['games'],**args);b=simulate_cfp(packet['teams'],packet['games'],**args)
    assert a==b==report['cfp'],'Default incumbent differs from deployed 10000-draw report'
    bounds(a['teams'])
    return {'draws':10000,'sameSeedRepeat':'exact','deployedReport':'exact'}
run('production-10000-draw-reproducibility-and-parity',production)
def reject_invalid():
    rejected=[]
    for label,mutate,choice,clock in [
        ('unknown-game',lambda x:x,{'unknown':'Texas'},now),
        ('nonparticipant',lambda x:x,{str(g['game_id']):'Alabama'},now),
        ('started-game',lambda x:x,choices[1],'2027-01-01T00:00:00Z'),
        ('duplicate-game',lambda x:x['games'].append(x['games'][0]),{},now),
        ('nonfinite-rating',lambda x:x['teams'][next(iter(x['teams']))].update(rating=float('nan')),{},now),
    ]:
        x=deepcopy(packet);mutate(x)
        try:simulate_scenario(x,choice,now=clock)
        except (ValueError,TypeError,KeyError):rejected.append(label)
        else:raise AssertionError('Invalid Python input accepted: '+label)
    return rejected
run('invalid-python-inputs-rejected',reject_invalid)
(OUT/'monte-carlo-results.json').write_text(json.dumps({'productionCommit':'2c47bec5935fd32844ef20c307e3aab4c201d052','elapsedSeconds':time.monotonic()-start,'scenarioCases':len(runs),'records':records},indent=2)+'\n')
print(json.dumps(records,indent=2))
if any(r['status']=='FAIL' for r in records):raise SystemExit(1)
