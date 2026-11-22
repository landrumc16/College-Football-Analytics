// "Why this prediction?" helper: exact sums, Texas Tech at Baylor audit case, worse-record and neutral cases, no filler.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = { exports: {} }
vm.runInNewContext(ts.transpileModule(await readFile('web/src/predictionExplanations.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: m.exports, Math, Number, Object, String })
const s = m.exports
const results = []
const check = (name, fn) => { fn(); results.push(name) }

check('bottom line names the main reason, an even season and what works against the favourite', () => {
  assert.equal(s.bottomLine('Texas Tech', 'Baylor', 'Baylor', { season: -0.38, prior: 4.46, home: -3.0 }),
    "Texas Tech's carry-over from last season is the main reason Texas Tech is favored; this season's games alone rate the teams almost even; Baylor's home field (3.0 points) works against Texas Tech.")
  assert.equal(s.bottomLine('Army', 'Navy', null, { season: 2.8, prior: 1.6, home: 0 }),
    "Army's stronger results this season are the main reason Army is favored, helped by Army's carry-over from last season.")
  assert.match(s.bottomLine('A', 'B', 'B', { season: -2.0, prior: 9.0, home: -3.0 }), /B's home field \(3\.0 points\) and B's stronger results this season \(2\.0 points\) work against A\.$/)
})

const data = JSON.parse(await readFile('web/public/prediction-explanations.json', 'utf8'))
const report = JSON.parse(await readFile('data/season-2026-report.json', 'utf8'))
const published = new Map(report.predictions.map(p => [p.game_id, p]))
const sameData = report.retrieved_at === data.report_retrieved_at
const AUDIT_SNAPSHOT = '2026-11-20T06:48:33.393964+00:00'

check('Texas Tech at Baylor reflects the published forecasts and the verified matchup audit', () => {
  const g = data.games.find(x => x.home === 'Baylor' && x.away === 'Texas Tech')
  // The audit is a point-in-time analysis of one pregame snapshot; later refreshes legitimately move these numbers.
  if (!g || data.data_retrieved_at !== AUDIT_SNAPSHOT) { results.push('Texas Tech at Baylor audit wording applies only to the audited snapshot; sums and wording rules are checked for every game'); return }
  const e = s.explain(g, data)
  assert.equal(e.favourite, 'Texas Tech')
  assert.match(e.headline, /^Official forecast: Texas Tech by 1\.1 points\. Standard: Texas Tech by 0\.9\. Momentum: Texas Tech by 2\.3\.$/)
  assert.match(e.bottomLine, /carry-over from last season is the main reason Texas Tech is favored; this season's games alone rate the teams almost even; Baylor's home field \(3\.0 points\) works against Texas Tech/)
  const official = e.models.find(r => r.model === 'Official')
  assert.ok(Math.abs(official.prior - 4.46) < 0.01 && Math.abs(official.season + 0.38) < 0.01 && official.home === -3, JSON.stringify(official))
  const text = e.factors.map(f => f.text).join(' ')
  assert.match(text, /This season's games: 0\.4 points toward Baylor\. Carry-over from last season: 4\.5 points toward Texas Tech\./)
  assert.match(text, /Baylor has played the tougher schedule/)
  assert.match(text, /moves the forecast 1\.4 points toward Texas Tech/)
  assert.match(text, /Baylor is at home, worth 3\.0 points in the official model and 3\.3 in Standard and Momentum/)
  assert.ok(e.notes.some(n => /33–10 win over FCS Abilene Christian counts as its weakest game/.test(n)), e.notes.join('|'))
  assert.ok(e.unavailable.some(u => /Quarterback/.test(u)))
})

check('every explained game: parts add up to each published forecast, no filler, appropriate variety', () => {
  const bottoms = new Set(), matchups = new Set()
  for (const g of data.games) {
    const e = s.explain(g, data)
    assert.ok(e, `game ${g.game_id} explained`)
    for (const r of e.models) assert.ok(Math.abs(r.season + r.prior + r.home - r.total) < 0.01, `${g.game_id} ${r.model} parts`)
    const sign = e.favourite === g.home ? 1 : -1
    assert.ok(Math.abs(e.models[0].total * sign - g.official.home_margin) < 1e-9)
    if (sameData) assert.ok(Math.abs(g.official.home_margin - published.get(g.game_id).home_margin) < 0.001, `official margin ${g.game_id}`)
    const all = [e.bottomLine, e.headline, e.modelDifference, ...e.factors.map(f => f.text), ...e.notes].join(' ')
    assert.ok(!/undefined|NaN|null|Infinity/.test(all), all)
    assert.equal(e.factors.length, 5)
    assert.ok(e.factors.find(f => f.key === 'home').text.includes(g.neutral_site ? 'Neutral site' : `${g.home} is at home`))
    bottoms.add(e.bottomLine); matchups.add(e.factors.find(f => f.key === 'matchup').text)
  }
  assert.equal(matchups.size, data.games.length, 'every matchup explanation is specific to its game')
  assert.ok(bottoms.size >= data.games.length * 0.9, `bottom lines are specific (${bottoms.size} of ${data.games.length})`)
  results.push(`real file: ${data.games.length} games, ${bottoms.size} distinct bottom lines${sameData ? ', official margins equal the season report' : ''}`)
})

check('a favourite with the worse record is explained; small gaps are not over-explained', () => {
  const worse = data.games.map(g => [g, s.explain(g, data)]).find(([, e]) => {
    const f = data.teams[e.favourite], u = data.teams[e.underdog]; return f.wins / (f.wins + f.losses) < u.wins / (u.wins + u.losses) })
  if (worse) assert.match(worse[1].factors.find(f => f.key === 'schedule').text, /is favored despite the worse record/)
  const agree = data.games.map(g => s.explain(g, data)).find(e => Math.max(...e.models.map(r => r.total)) - Math.min(...e.models.map(r => r.total)) < 0.9)
  if (agree) assert.equal(agree.modelDifference, 'All three forecasts agree to within a point.')
})

check('a game without team data returns no explanation (the card keeps its published summary)', () => {
  assert.equal(s.explain({ ...data.games[0], home: 'Unknown U' }, data), null)
})
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
