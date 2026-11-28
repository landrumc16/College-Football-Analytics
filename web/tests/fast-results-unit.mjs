import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = {exports:{}}
vm.runInNewContext(ts.transpileModule(await readFile('web/src/fastResults.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:m.exports,Date,Number,Object,String,Set,URL})
const parse=m.exports.parseFastResults
const teams=['Texas Tech','TCU'], now=Date.parse('2026-11-28T00:00:00Z')
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
