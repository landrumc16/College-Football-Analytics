// Three-score strength: fixtures plus TypeScript <-> Python parity on the real published season report.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { readFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import vm from 'node:vm'
import ts from 'typescript'

const source = await readFile('web/src/strengthScores.ts', 'utf8')
const module = { exports: {} }
vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: module.exports, Number, Math, Object })
const s = new Proxy(module.exports, { get: (t, k) => typeof t[k] === 'function' ? (...a) => { const r = t[k](...a); return r && typeof r === 'object' ? structuredClone(r) : r } : t[k] })
const results = []
const check = (name, fn) => { fn(); results.push(name) }
const close = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`)
const g = (week, home, away, hs, as_) => ({ week, home, away, completed: true, home_score: hs, away_score: as_ })

check('engine-identical adjusted margin', () => {
  assert.equal(s.adjustedHomeMargin(31, 20), 8); assert.equal(s.adjustedHomeMargin(70, 0), 45); assert.equal(s.adjustedHomeMargin(0, 70), -45)
})
check('momentum = mean of the latest three opponent-adjusted results only', () => {
  const sched = [g(1, 'A', 'B', 0, 50), g(2, 'C', 'A', 10, 20), g(3, 'A', 'FCS U', 40, 10), g(4, 'A', 'B', 24, 21)]
  const r = s.strengthScores('A', 6, { B: 2, C: -4 }, sched)
  // week 2 away at C: -(10-20-3)=13 + (-4) = 9; week 3 home vs FCS: (27) + (-26) = 1; week 4 home vs B: 0 + 2 = 2
  close(r.momentum, (9 + 1 + 2) / 3); close(r.combined, 0.8 * 6 + 0.2 * 4); assert.equal(r.direction, 'steady')   // -2 is within the +/-7 band
  assert.equal(r.momentumGames, 3)
})
check('fewer than three games: no momentum, combined = season', () => {
  const r = s.strengthScores('A', 7, {}, [g(1, 'A', 'B', 21, 7), g(2, 'A', 'C', 21, 7)])
  assert.equal(r.momentum, null); assert.equal(r.combined, 7); assert.equal(r.direction, 'insufficient_data'); assert.equal(r.momentumGames, 2)
})
check('steady band, unplayed games ignored, weight 0 equals season', () => {
  const sched = [g(1, 'A', 'B', 13, 10), g(2, 'A', 'B', 13, 10), g(3, 'A', 'B', 13, 10), { week: 4, home: 'A', away: 'B', completed: false, home_score: null, away_score: null }]
  const r = s.strengthScores('A', 0.5, { B: 0 }, sched)       // each observation 0 -> delta -0.5 within the band
  assert.equal(r.direction, 'steady'); close(r.momentum, 0)
  close(s.strengthScores('A', 0.5, { B: 0 }, sched, 3, 0).combined, 0.5)
})

check('steady band is +/-7 rating points (about 1 SD of recent vs season)', () => {
  const three = obs => [g(1, 'A', 'B', obs + 3, 0), g(2, 'A', 'B', obs + 3, 0), g(3, 'A', 'B', obs + 3, 0)]   // each observation = obs
  assert.equal(s.STEADY_BAND, 7)
  assert.equal(s.strengthScores('A', 10, { B: 0 }, three(17)).direction, 'steady')
  assert.equal(s.strengthScores('A', 9.5, { B: 0 }, three(17)).direction, 'rising')
  assert.equal(s.strengthScores('A', 24.5, { B: 0 }, three(17)).direction, 'declining')
})
check('strength ranks give each score a familiar FBS scale', () => {
  const rankings = [{ team: 'A', rating: 10 }, { team: 'B', rating: 5 }, { team: 'C', rating: -2 }, { team: 'D', rating: 0 }]
  const sched = [g(1, 'C', 'B', 40, 0), g(2, 'C', 'A', 40, 0), g(3, 'C', 'B', 40, 0), g(1, 'A', 'B', 3, 0), g(3, 'A', 'B', 3, 0), g(4, 'D', 'B', 10, 7)]
  const r = s.rankedStrength(rankings, sched)
  assert.deepEqual([r.A.seasonRank, r.B.seasonRank, r.D.seasonRank, r.C.seasonRank], [1, 2, 3, 4])
  assert.equal(r.C.momentumRank, 1)                       // C won its last three by 40: best recent form despite the lowest season rating
  assert.equal(r.D.momentumRank, null)                    // one game: no momentum rank
  assert.deepEqual(new Set([r.A.momentumRank, r.B.momentumRank, r.C.momentumRank]), new Set([1, 2, 3]))
  assert.equal(r.C.teams, 4)
})
check('TypeScript matches the Python research function for every FBS team on the published report', () => {
  const py = spawnSync('python3', ['-c', `
import json, sys
from types import SimpleNamespace
sys.path.insert(0, 'src'); sys.path.insert(0, '.')
from cfb_analytics.ratings import Team, Game
from scripts.strength_blend_research import calculate_strength_components
r = json.load(open('data/season-2026-report.json'))
teams = [Team(t['team'], 'X', 0.0) for t in r['rankings']]
ratings = {t['team']: SimpleNamespace(adaptive_rating=t['rating']) for t in r['rankings']}
done = sorted((g for g in r['schedule'] if g['completed'] and g['home_score'] is not None), key=lambda g: (g['week'], g['game_id']))
games = [Game(g['home'], g['away'], g['home_score'], g['away_score'], g['week']) for g in done]
out = calculate_strength_components(teams, games, window=3, momentum_weight=0.2, season_ratings=ratings)
print(json.dumps({k: [v.season_strength, v.recent_momentum, v.combined_strength, v.direction, v.momentum_games] for k, v in out.items()}))
`], { encoding: 'utf8' })
  assert.equal(py.status, 0, py.stderr)
  const expected = JSON.parse(py.stdout)
  {
    const text = readFileSync('data/season-2026-report.json', 'utf8')
    const report = JSON.parse(text)
    const ratings = Object.fromEntries(report.rankings.map(t => [t.team, t.rating]))
    for (const t of report.rankings) {
      const mine = s.strengthScores(t.team, t.rating, ratings, report.schedule)
      const [season, momentum, combined, direction, games] = expected[t.team]
      close(mine.season, season); close(mine.combined, combined); assert.equal(mine.direction, direction, t.team); assert.equal(mine.momentumGames, Math.min(games, 3))
      if (momentum === null) assert.equal(mine.momentum, null); else close(mine.momentum, momentum)
    }
    results.push(`parity across ${report.rankings.length} teams`)
  }
})
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
