import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = {exports:{}}
vm.runInNewContext(ts.transpileModule(await readFile('web/src/fastResults.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:m.exports,Date,Number,Object,String,Set,Map,URL})
const parse=m.exports.parseFastResults
const teams=[{game_id:1,home:'Texas Tech',away:'TCU'}], now=Date.parse('2026-11-28T00:00:00Z')
const event={game_id:1,home:'Texas Tech',away:'TCU',home_score:48,away_score:27,status:'provisional',observed_at:'2026-11-27T20:00:00Z',verified_at:null,statistics_pending:true,source:'https://authorized.example/game/1',model_ingestion_allowed:false}
const fixture=()=>({schema_version:1,revision:1,generated_at:'2026-11-27T20:01:00Z',events:[{...event}],records:{'Texas Tech':{wins:11,losses:1,provisional_games:1}}})
assert.equal(parse(null,teams,now),null)
assert.ok(parse(fixture(),teams,now))
for(const change of [{home:'Unknown'},{away:'Texas Tech'},{home_score:-1},{away_score:48},{source:'javascript:alert(1)'},{observed_at:'2027-01-01T00:00:00Z'},{status:'final'},{model_ingestion_allowed:true}]) { const d=fixture();Object.assign(d.events[0],change);assert.equal(parse(d,teams,now),null,JSON.stringify(change)) }
let d=fixture();d.events.push({...event});assert.equal(parse(d,teams,now),null)
d=fixture();d.events[0].status='confirmed';assert.equal(parse(d,teams,now),null)
d.events[0].verified_at='2026-11-27T21:00:00Z';d.events[0].model_ingestion_allowed=true;assert.ok(parse(d,teams,now))
d.events[0].status='disputed';assert.ok(parse(d,teams,now));d.events[0].verified_at=null;assert.equal(parse(d,teams,now),null)
d=fixture();d.records['Texas Tech'].wins=-1;assert.equal(parse(d,teams,now),null)
d=fixture();d.generated_at='2026-11-27';assert.equal(parse(d,teams,now),null)
console.log('Fast results: valid provisional/confirmed, missing feed, identities, score, URL, timestamps, duplicates, model gating and records passed')

// Exercise the real retained national schedule, including FCS opponents and records,
// through the Python public publisher and the actual frontend contract.
const {spawnSync} = await import('node:child_process')
const archived = JSON.parse(await readFile('data/season-2026-report.json','utf8'))
const result=spawnSync(process.env.PYTHON || 'python',['-c',`
import json
from cfb_analytics.rapid_results import transition, public_snapshot
r=json.load(open('data/season-2026-report.json'))
fbs={x['team'] for x in r['rankings']}
g=next(g for g in r['schedule'] if g['home'] not in fbs or g['away'] not in fbs)
o=dict(kind='game_final', game_id=g['game_id'], home=g['home'], away=g['away'], home_score=g.get('home_score') if g.get('completed') else 30, away_score=g.get('away_score') if g.get('completed') else 10, status='final', source='https://licensed.example/finals', published_at='2026-11-26T20:00:00Z',observed_at='2026-11-26T20:01:00Z')
s=transition(None,o,r['schedule'],{'https://licensed.example/finals':'licensed'})
print(json.dumps(public_snapshot(s,r['schedule'])))
`],{encoding:'utf8',env:{...process.env,PYTHONPATH:'src'}})
assert.equal(result.status,0,result.stderr)
const actual=JSON.parse(result.stdout)
assert.ok(parse(actual,archived.schedule), 'Real publisher with archived FCS records must display')
const mismatch=structuredClone(actual);[mismatch.events[0].home,mismatch.events[0].away]=[mismatch.events[0].away,mismatch.events[0].home]
assert.equal(parse(mismatch,archived.schedule),null,'Cannot reverse canonical game identity')
const unknown=structuredClone(actual);unknown.events[0].game_id='not-on-schedule'
assert.equal(parse(unknown,archived.schedule),null,'Unknown game cannot borrow valid team names')
console.log('Archived national publisher/frontend integration, FCS game and canonical identity rejection passed')
