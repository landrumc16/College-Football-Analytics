import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import ts from 'typescript'
const source=await readFile('web/src/scenarios.ts','utf8')
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText
const {simulate}=await import('data:text/javascript,'+encodeURIComponent(js))
const fixture=JSON.parse(await readFile('research/v6/scenario-python-fixtures.json','utf8'))
for(const c of fixture.cases){
 const result=simulate(fixture.input,c.overrides,fixture.now)
 assert.deepEqual(result.teams,c.teams,'Browser algorithm must match retained Python simulation exactly')
 assert.ok(Math.abs(result.teams.reduce((s,t)=>s+t.cfp_field,0)-12)<.003)
 assert.ok(Math.abs(result.teams.reduce((s,t)=>s+t.national_title,0)-1)<.003)
}
const base=simulate(fixture.input,{},fixture.now)
assert.deepEqual(base.teams,simulate(fixture.input,{},fixture.now).teams)
for(const choices of [{'no-game':'Texas'},{[fixture.input.games[0].game_id]:'not-participant'}])assert.throws(()=>simulate(fixture.input,choices,fixture.now))
assert.throws(()=>simulate(fixture.input,fixture.cases[1].overrides,'2027-01-01T00:00:00Z'))
const report=JSON.parse(await readFile('data/season-2026-report.json','utf8'))
// Retained parity fixtures stay immutable; compare live odds with the matching live packet.
const currentInput=JSON.parse(await readFile('web/public/v6-scenario-input.json','utf8'))
const currentBaseline=simulate(currentInput,{},new Date().toISOString())
const published=new Map(report.cfp.teams.map(t=>[t.team,t]))
let maxDifference=0
for(const t of currentBaseline.teams)for(const key of ['cfp_field','conference_title'])maxDifference=Math.max(maxDifference,Math.abs(t[key]-published.get(t.team)[key]))
assert.ok(maxDifference<=.05,`Baseline exceeds predeclared 5pp tolerance: ${maxDifference}`)
console.log(JSON.stringify({pythonBrowserParity:'exact',cases:fixture.cases.length,draws:fixture.input.draws,reset:'exact',maxPublishedProbabilityDifference:maxDifference,unthrottledNodeMs:base.milliseconds}))
