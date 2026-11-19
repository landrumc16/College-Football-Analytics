// V8 Offense & Defense helpers: formatting, matchup expectations and edges, leaderboards (fixtures + real data).
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = { exports: {} }
vm.runInNewContext(ts.transpileModule(await readFile('web/src/v8Stats.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: m.exports, Math, Number, Object })
const s = m.exports
const results = []
const check = (name, fn) => { fn(); results.push(name) }
const row = (raw, adj, rank) => [raw, rank, null, null, 0, adj, 0.01, rank, 100]
const defs = { sr: { label: 'Success rate', offense_higher_is_better: true }, sack: { label: 'Sack rate', offense_higher_is_better: false } }
const fixture = { fbs_teams: 3, power_teams: 2, league: { sr: { mean: 0.40 }, sack: { mean: 0.06 } }, definitions: defs,
  teams: { A: { conference: 'SEC', offense: { sr: row(0.5, 0.48, 1), sack: row(0.04, 0.04, 1) }, defense: { sr: row(0.3, 0.32, 1), sack: row(0.09, 0.09, 1) } },
           B: { conference: 'SEC', offense: { sr: row(0.4, 0.40, 2), sack: row(0.06, 0.06, 2) }, defense: { sr: row(0.4, 0.40, 2), sack: row(0.06, 0.06, 2) } },
           C: { conference: 'MAC', offense: { sr: row(0.3, 0.32, 3), sack: row(0.08, 0.08, 3) }, defense: { sr: row(0.5, 0.48, 3), sack: row(0.03, 0.03, 3) } } } }
check('formatting: rates as percentages, N/A for missing', () => {
  assert.equal(s.format('sr', 0.4567), '45.7%'); assert.equal(s.format('ppd', 2.345), '2.35'); assert.equal(s.format('epa', 0.1234), '0.12')
  assert.equal(s.format('sr', null), 'N/A'); assert.equal(s.format('ypp', NaN), 'N/A')
})
check('expected = offense + defense - mean (additive model)', () => {
  assert.ok(Math.abs(s.expected(fixture, 'sr', 'A', 'C') - (0.48 + 0.48 - 0.40)) < 1e-12)
  assert.equal(s.expected(fixture, 'sr', 'A', 'Nobody'), null)
})
check('edges favour the right side and lower-is-better metrics flip', () => {
  const edges = s.matchupEdges(fixture, 'A', 'C', ['sr', 'sack'])
  const aSr = edges.find(e => e.offense === 'A' && e.metric === 'sr'), cSack = edges.find(e => e.offense === 'C' && e.metric === 'sack')
  assert.ok(aSr.size > 0 && aSr.favours === 'A')
  assert.ok(cSack.size < 0)   // C's offense allows sacks (8%) and A's defense creates them (9%): defense edge
  assert.equal(cSack.favours, 'A')
  assert.ok(s.describeEdge(aSr).startsWith('Clear edge for A\'s offense'))
})
check('notable edges need half a standard deviation', () => {
  const calm = { ...fixture, teams: { A: fixture.teams.B, B: fixture.teams.B, C: fixture.teams.A } }
  assert.equal(s.notableEdges(s.matchupEdges(calm, 'A', 'B', ['sr'])).length, 0)
})
check('leaderboard ordering and power pool', () => {
  assert.deepEqual(s.leaderboard(fixture, 'sr', 'offense', 'adjusted').map(r => r.team), ['A', 'B', 'C'])
  assert.equal(s.leaderboard(fixture, 'sr', 'offense', 'power').length, 0)
  assert.equal(s.poolSize(fixture, 'power'), 2)
  assert.equal(s.percentile(1, 138), 100); assert.equal(s.percentile(138, 138), 0)
})
const data = JSON.parse(await readFile('web/public/v8-team-stats.json', 'utf8'))
assert.equal(Object.keys(data.teams).length, data.fbs_teams)
for (const metric of Object.keys(data.definitions)) {
  const ranks = s.leaderboard(data, metric, 'offense', 'adjusted').map(r => r.rank)
  assert.equal(ranks.length, data.fbs_teams, metric); assert.equal(ranks[0], 1)
  assert.equal(s.leaderboard(data, metric, 'defense', 'power').length, data.power_teams, metric)
}
results.push('real published file: every FBS team ranked, power pool complete')
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
