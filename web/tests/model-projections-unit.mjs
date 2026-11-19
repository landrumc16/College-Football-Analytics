// Dual model projection helpers: score lines, favourites, disagreement explanations, likely records (fixtures + real file).
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = { exports: {} }
vm.runInNewContext(ts.transpileModule(await readFile('web/src/modelProjections.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: m.exports, Math, Number, Object, Set, String })
const s = m.exports
const results = []
const check = (name, fn) => { fn(); results.push(name) }
const proj = (hp, ap, p) => ({ home_points: hp, away_points: ap, home_margin: hp - ap, home_win_probability: p })
const game = (std, mom, homeForm, awayForm) => ({ game_id: 1, week: 12, start_date: null, home: 'Baylor', away: 'Texas Tech', neutral_site: false,
  home_fbs: true, away_fbs: true, home_form: homeForm, away_form: awayForm, standard: std, momentum: mom, official: null })
const data = { teams: { Baylor: { standard: { rating: 4 } }, 'Texas Tech': { standard: { rating: 12 } } } }

check('score line puts the projected winner first; favourite and probability', () => {
  const g = game(proj(28.0, 28.9, 0.476), proj(28.7, 31.0, 0.441), 5, 16)
  assert.equal(s.scoreLine(g, 'standard'), 'Texas Tech 29, Baylor 28')
  assert.deepEqual({ ...s.favourite(g, 'momentum') }, { team: 'Texas Tech', probability: 1 - 0.441 })
  assert.equal(s.pct(0.5589), '56%'); assert.equal(s.pct(null), 'N/A')
})
check('agreement within a point is stated plainly', () => {
  assert.equal(s.disagreement(game(proj(28, 29, 0.47), proj(28.2, 29, 0.48), 4, 12), data).summary, 'The models agree to within a point.')
})
check('short summary names the side Momentum favours and a consistent cause; calculation in details', () => {
  // Momentum shifts 1.35 toward Texas Tech (away); Texas Tech's recent form is 4 above its season level.
  const e = s.disagreement(game(proj(28.0, 28.9, 0.476), proj(28.7, 31.0, 0.441), 4, 16), data)
  assert.equal(e.summary, 'Momentum favors Texas Tech by 1.4 additional points based on stronger recent opponent-adjusted performance.')
  assert.ok(e.summary.length < 120)
  assert.ok(e.details.some(d => d === 'Standard margin: Texas Tech by 0.9. Momentum margin: Texas Tech by 2.3.'), e.details)
  assert.ok(e.details.some(d => d.startsWith('Texas Tech: last three games +16.0 per game vs a season rating of +12.0')), e.details)
})
check('a slump by the other team is described as such; an inconsistent driver is never used', () => {
  // Shift toward Texas Tech explained by Baylor's slump (home form 1 vs season 4).
  assert.equal(s.disagreement(game(proj(28.0, 28.9, 0.476), proj(28.7, 31.0, 0.441), 1, 12), data).summary,
    "Momentum favors Texas Tech by 1.4 additional points based on Baylor's weaker recent opponent-adjusted performance.")
  // Shift toward Texas Tech, but the only form change is a Baylor surge (would favour Baylor): fall back.
  const e = s.disagreement(game(proj(28.0, 28.9, 0.476), proj(28.7, 31.0, 0.441), 9, 12), data)
  assert.equal(e.summary, 'Momentum favors Texas Tech by 1.4 additional points because recent games count more.')
})
check('tiebreak note names the swapped contenders, and is absent otherwise', () => {
  assert.equal(s.tiebreakNote('Texas Tech', { tiebreak_swaps: [{ rival: 'BYU', standard_gap: -0.9, momentum_gap: 0.21 }] }),
    'Playoff odds differ partly because Texas Tech and BYU swap order between the models, and tied conference records go to the higher-rated team.')
  assert.match(s.tiebreakNote('A', { tiebreak_swaps: [{ rival: 'B' }, { rival: 'C' }] }), /A and B and C swap/)
  assert.equal(s.tiebreakNote('A', { tiebreak_swaps: [] }), null)
  assert.equal(s.tiebreakNote('A', {}), null)
})
check('most likely record from the distribution', () => {
  const t = { wins: 9, losses: 1, standard: { win_distribution: [0.05, 0.35, 0.6] } }
  assert.deepEqual({ ...s.likelyRecord(t, 'standard') }, { wins: 11, losses: 1, probability: 0.6 })
})
const real = JSON.parse(await readFile('web/public/dual-projections.json', 'utf8'))
for (const g of real.games) for (const k of ['standard', 'momentum']) assert.ok(s.scoreLine(g, k).includes(g.home) && s.disagreement(g, real).summary.length > 20 && s.disagreement(g, real).summary.length <= 160)
assert.deepEqual([...s.weeks(real)], [...new Set(real.games.map(g => g.week))].sort((a, b) => a - b))
results.push(`real published file: ${real.games.length} games explained, weeks ${s.weeks(real).join(', ')}`)
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
