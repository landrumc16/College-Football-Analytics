// Plain-English takeaways: wording thresholds, cautious language, and agreement with the real published numbers.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = { exports: {} }
vm.runInNewContext(ts.transpileModule(await readFile('web/src/statTakeaways.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: m.exports, Math, Map, Number, Object, String })
const t = m.exports, results = []
const check = (name, fn) => { fn(); results.push(name) }

check('performance vs expectations: graded wording and small-sample caveat', () => {
  assert.equal(t.expectationTakeaway('Texas Tech', 0.88, 3), 'Texas Tech is slightly ahead of expectations, though 3 tracked games are a small sample.')
  assert.equal(t.expectationTakeaway('A', 0.1, 8), 'A is right in line with expectations.')
  assert.equal(t.expectationTakeaway('A', -1.4, 8), 'A is behind expectations.')
  assert.equal(t.expectationTakeaway('A', 2.6, 9), 'A is well ahead of expectations.')
  assert.match(t.expectationTakeaway('A', 0.5, 1), /1 tracked game is a small sample/)
})
check('season outlook and profile vs polls', () => {
  assert.equal(t.outlookTakeaway('A', 10, 10.3), 'A is projected for about 10.3 wins: 10 so far and roughly 0.3 more from its remaining games.')
  assert.equal(t.outlookTakeaway('A', 9, 9), 'A has finished its regular season with 9 wins.')
  assert.match(t.profileTakeaway('A', 8, 12, 11, true), /broadly agree on A \(model No\. 8, the AP poll No\. 12\)/)
  assert.match(t.profileTakeaway('A', 33, 17, 18, true), /rates A lower than the AP poll does \(model No\. 33, poll No\. 17\)/)
  assert.match(t.profileTakeaway('A', 20, null, null, true), /ranks A No\. 20 even though it is unranked in both polls/)
  assert.equal(t.profileTakeaway('A', 5, null, null, false), 'A is No. 5 in our model.')
})
check('polls, playoffs, forecasts and report cards', () => {
  const ap = [{ team: 'X', rank: 1 }, { team: 'Y', rank: 2 }, { team: 'Z', rank: 3 }], co = [{ team: 'Y', rank: 1 }, { team: 'X', rank: 2 }, { team: 'W', rank: 3 }]
  assert.equal(t.pollTakeaway(ap, co), 'The AP and Coaches polls share 2 of their 25 teams and order them very similarly.')
  assert.equal(t.cfpTakeaway([{ team: 'A', cfp_field: 1 }, { team: 'B', cfp_field: 0.97 }, { team: 'C', cfp_field: 0.55 }, { team: 'D', cfp_field: 0.3 }]),
    '2 teams make the field in at least 95% of simulated seasons; C is closest to the bubble at 55%.')
  assert.match(t.forecastTakeaway(20, 0.19, 0.25), /more accurate than a coin flip/)
  assert.match(t.forecastTakeaway(20, 0.26, 0.25), /not more accurate than a coin flip/)
  assert.equal(t.reportCardTakeaway('A', [{ label: 'Hype Index', score: 40, grade: 'C' }, { label: 'Program Strength', score: 91, grade: 'A' }]),
    "A's strongest graded category is Program Strength (A); its weakest is Hype Index (C).")
  assert.equal(t.reportCardTakeaway('A', [{ label: 'Hype Index', score: null, grade: null }]), null)
})

const report = JSON.parse(await readFile('data/season-2026-report.json', 'utf8'))
const polls = JSON.parse(await readFile('data/poll-2026-snapshot.json', 'utf8'))
check('takeaways agree with the real published numbers', () => {
  const top = [...report.rankings].sort((a, b) => a.rank - b.rank)
  const r = t.rankingsTakeaway(report.rankings)
  assert.ok(r.startsWith(`${top[0].team} leads our rankings.`) && r.includes((top[0].rating - top[9].rating).toFixed(1)), r)
  const c = t.cfpTakeaway(report.cfp.teams)
  const locks = report.cfp.teams.filter(x => x.cfp_field >= 0.95).length
  assert.ok(c.startsWith(`${locks} teams make the field`), c)
  for (const [team, p] of Object.entries(report.performance)) if (p.games_with_forecasts > 0) {
    const s = t.expectationTakeaway(team, p.wins_above_expected, p.games_with_forecasts)
    assert.ok(p.wins_above_expected >= 0.25 ? /ahead/.test(s) : p.wins_above_expected <= -0.25 ? /behind/.test(s) : /in line/.test(s), `${team}: ${s}`)
  }
  assert.ok(t.pollTakeaway(polls.ap_top25, polls.coaches_top25).startsWith('The AP and Coaches polls share'))
  for (const s of [r, c]) assert.ok(!/undefined|NaN|null/.test(s))
})
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
