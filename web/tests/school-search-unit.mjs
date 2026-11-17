// School search ranking: exact > abbreviation > prefix > word prefix > partial; accents, case and limits.
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = { exports: {} }
vm.runInNewContext(ts.transpileModule(await readFile('web/src/schoolSearch.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: m.exports, Number, Math, Object, Set, String })
const s = m.exports
const report = JSON.parse(await readFile('data/season-2026-report.json', 'utf8'))
const fbs = report.rankings.map(t => t.team)
const results = []
const check = (name, fn) => { fn(); results.push(name) }
const rank = q => JSON.parse(JSON.stringify(s.rankSchools(q, fbs)))
check('"Tex" lists Texas schools, prefix matches first, Texas Tech included', () => {
  const r = rank('Tex'); assert.ok(r.includes('Texas Tech')); const firstNonPrefix = r.findIndex(n => !n.startsWith('Tex'))
  assert.ok(firstNonPrefix === -1 || r.slice(firstNonPrefix).every(n => !n.startsWith('Tex')), r.join(','))   // prefix tier before word-prefix
  assert.ok(r.indexOf('Texas Tech') < r.indexOf('North Texas'))
  assert.equal(rank('texas')[0], 'Texas')                          // exact beats prefix
})
check('TCU and LSU: exact, case-insensitive', () => { assert.equal(rank('tcu')[0], 'TCU'); assert.equal(rank('LSU')[0], 'LSU') })
check('verified abbreviations only apply to schools in the list', () => {
  assert.equal(rank('TTU')[0], 'Texas Tech'); assert.equal(rank('uga')[0], 'Georgia')
  assert.deepEqual(rank('OSU').slice(0, 3), ['Ohio State', 'Oklahoma State', 'Oregon State'])
  assert.deepEqual(JSON.parse(JSON.stringify(s.rankSchools('TTU', ['Georgia']))), [])
})
check('word prefix and partial matches; accents ignored', () => {
  assert.ok(rank('state').length > 0 && rank('state').length <= s.MAX_SUGGESTIONS)
  assert.equal(rank('san jose')[0], 'San José State')
  assert.ok(rank('a&m').includes('Texas A&M'))
  assert.ok(rank('Tech').indexOf('Texas Tech') >= 0)               // word prefix
})
check('empty and no-match queries', () => { assert.deepEqual(rank(''), []); assert.deepEqual(rank('   '), []); assert.deepEqual(rank('zzzz'), []) })
check('every FBS school finds itself first by full name', () => { for (const t of fbs) assert.equal(rank(t)[0], t, t) })
check('exactSchool for confirm-later pickers', () => {
  assert.equal(s.exactSchool('texas tech', fbs), 'Texas Tech'); assert.equal(s.exactSchool('Texas Te', fbs), null)
})
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
