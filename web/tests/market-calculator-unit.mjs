// Independent mathematical fixtures for the Market Analysis Calculator (hand-computed expectations).
import assert from 'node:assert/strict'
import {readFile} from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'

const source = await readFile('web/src/marketCalculator.ts', 'utf8')
const code = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022}}).outputText
const module = {exports: {}}
vm.runInNewContext(code, {exports: module.exports, Number, Math, String, RangeError})
// Copy sandbox objects into this realm (structuredClone keeps -0) so strict deep equality compares values only.
const c = new Proxy(module.exports, {get: (target, key) => (...args) => { const r = target[key](...args); return r && typeof r === 'object' ? structuredClone(r) : r }})
const results = []
const check = (name, fn) => { fn(); results.push(name) }
const close = (a, b, eps = 1e-12) => assert.ok(Math.abs(a - b) < eps, `${a} != ${b}`)

check('moneyline raw implied probability (no vig removal)', () => {
  close(c.moneylineProbability(-150), 150 / 250)          // 0.6
  close(c.moneylineProbability(130), 100 / 230)           // 0.43478...
  close(c.moneylineProbability(100), 0.5)
  close(c.moneylineProbability(-100), 0.5)
  close(c.moneylineProbability(-110), 110 / 210)          // 0.5238...
  close(c.moneylineProbability(-110) * 2, 220 / 210)       // both sides at -110 sum above 100%: vig retained
  close(c.moneylineProbability(-10000), 10000 / 10100)
  close(c.moneylineProbability(2500), 100 / 2600)
  for (const bad of [99, -99, 0, 50, NaN, Infinity]) assert.throws(() => c.moneylineProbability(bad), RangeError)
})

check('moneyline parsing boundaries', () => {
  assert.deepEqual(c.parseMoneyline('+150'), {ok: true, value: 150})
  assert.deepEqual(c.parseMoneyline(' -110 '), {ok: true, value: -110})
  assert.deepEqual(c.parseMoneyline('−200'), {ok: true, value: -200})   // typographic minus
  assert.deepEqual(c.parseMoneyline('100'), {ok: true, value: 100})
  assert.deepEqual(c.parseMoneyline('-100'), {ok: true, value: -100})
  for (const bad of ['99', '-99.5', '0', '+0', 'abc', '1e3', '--110', '+', '-', '100000.5', 'Infinity', 'NaN'])
    assert.equal(c.parseMoneyline(bad).ok, false, bad)
  assert.deepEqual(c.parseMoneyline('   '), {ok: false, empty: true})
})

check('spread parsing, pick\'em and zero', () => {
  assert.deepEqual(c.parseSpread('-7'), {ok: true, value: -7})
  assert.deepEqual(c.parseSpread('+3.5'), {ok: true, value: 3.5})
  assert.deepEqual(c.parseSpread('PK'), {ok: true, value: 0})
  assert.deepEqual(c.parseSpread("pick'em"), {ok: true, value: 0})
  assert.deepEqual(c.parseSpread('-0'), {ok: true, value: 0})
  assert.ok(Object.is(c.parseSpread('-0').value, 0))
  assert.deepEqual(c.parseSpread('99.5'), {ok: true, value: 99.5})
  for (const bad of ['100', '-100', 'seven', '7-', '', '1,5']) assert.equal(c.parseSpread(bad).ok, false, bad)
  assert.deepEqual(c.parseSpread(''), {ok: false, empty: true})
})

check('probability parsing 0-100 inclusive', () => {
  assert.deepEqual(c.parseProbability('62'), {ok: true, value: 0.62})
  assert.deepEqual(c.parseProbability('62.5%'), {ok: true, value: 0.625})
  assert.deepEqual(c.parseProbability('0'), {ok: true, value: 0})
  assert.deepEqual(c.parseProbability('100'), {ok: true, value: 1})
  for (const bad of ['100.1', '-1', '+5', 'abc', '1e2', '50%%']) assert.equal(c.parseProbability(bad).ok, false, bad)
})

check('team perspective reverses margin and probability', () => {
  assert.deepEqual(c.teamView('Texas Tech', 0.75, 10.5, 'Texas Tech'), {probability: 0.75, margin: 10.5})
  const other = c.teamView('Texas Tech', 0.75, 10.5, 'Baylor')
  close(other.probability, 0.25); assert.equal(other.margin, -10.5)
  assert.ok(Object.is(c.teamView('A', 0.5, 0, 'B').margin, 0))
  for (const [p, m] of [[NaN, 3], [1.2, 3], [-0.1, 3], [0.6, NaN], [0.6, Infinity]]) assert.equal(c.teamView('A', p, m, 'A'), null)
})

check('spread comparison signs: favourites, underdogs, pick\'em', () => {
  // Model: team by 10; entered -7 (team favoured by 7) -> model 3 points more favourable.
  assert.equal(c.spreadDifference(10, -7), 3)
  // Model: team by 3; entered -7 -> model 4 points less favourable.
  assert.equal(c.spreadDifference(3, -7), -4)
  // Model: team loses by 4; entered +6.5 (underdog) -> model 2.5 more favourable.
  assert.equal(c.spreadDifference(-4, 6.5), 2.5)
  // Model: team loses by 4; entered +2 -> model 2 less favourable.
  assert.equal(c.spreadDifference(-4, 2), -2)
  // Pick'em.
  assert.equal(c.spreadDifference(2.5, 0), 2.5)
  // Perspective symmetry: the other team's view is the exact negative.
  for (const [m, s] of [[10, -7], [-4, 6.5], [0, 0], [1.25, -3]]) assert.ok(c.spreadDifference(-m, -s) === -c.spreadDifference(m, s))   // === treats -0 and 0 as equal; display uses signed()
})

check('probability differences in percentage points', () => {
  close(c.probabilityDifference(0.7, 0.62), 8)
  close(c.probabilityDifference(0.4, 0.6), -20)
  close(c.probabilityDifference(0.6, c.moneylineProbability(-150)), 0)
  close(c.probabilityDifference(1 - 0.7, 1 - 0.62), -8)        // reversed perspective
})

check('formatting never shows negative zero', () => {
  assert.equal(c.signed(0), '0.0'); assert.equal(c.signed(-0.04), '0.0'); assert.equal(c.signed(-0), '0.0')
  assert.equal(c.signed(3), '+3.0'); assert.equal(c.signed(-2.55, 1), '-2.5') ; assert.equal(c.signed(150, 0), '+150')
  assert.equal(c.percent(0.6), '60.0%')
})

check('plain-English explanations', () => {
  assert.equal(c.explainSpread('Texas Tech', 10, -7), 'Our model projects Texas Tech to win by 10.0 points. The entered spread makes Texas Tech a 7.0-point favourite. The model is 3.0 points more favourable to Texas Tech than the entered spread.')
  assert.equal(c.explainSpread('Baylor', -10, 7), 'Our model projects Baylor to lose by 10.0 points. The entered spread makes Baylor a 7.0-point underdog. The model is 3.0 points less favourable to Baylor than the entered spread.')
  assert.equal(c.explainSpread('A', 0, 0), "Our model projects an even game for A. The entered spread is a pick'em: neither team is favoured. The model and the entered spread agree.")
  assert.match(c.explainSpread('A', 1, -1), /1\.0-point favourite/)
  assert.equal(c.explainProbability('A', 0.7, 0.62, 'prediction market'), 'Our model gives A a 70.0% chance to win; the entered prediction-market probability is 62.0%. Our model is 8.0 percentage points higher.')
  assert.equal(c.explainProbability('A', 0.6, 0.6, 'moneyline'), 'Our model gives A a 60.0% chance to win; the raw probability implied by the entered moneyline is 60.0%. They match.')
  for (const text of [c.explainSpread('A', 10, -7), c.explainProbability('A', 0.7, 0.5, 'moneyline')])
    assert.doesNotMatch(text, /profit|bet |wager|value|edge|lock/i)
})

check('switching team re-expresses the same entered market', () => {
  assert.equal(c.flipSpreadInput('-7'), '+7'); assert.equal(c.flipSpreadInput('+3.5'), '-3.5')
  assert.equal(c.flipSpreadInput('PK'), '0'); assert.equal(c.flipSpreadInput('0.25'), '-0.25')
  assert.equal(c.flipSpreadInput('bad'), 'bad'); assert.equal(c.flipSpreadInput(''), '')
  assert.equal(c.flipProbabilityInput('62'), '38'); assert.equal(c.flipProbabilityInput('62.5%'), '37.5')
  assert.equal(c.flipProbabilityInput('0'), '100'); assert.equal(c.flipProbabilityInput('x'), 'x')
})

check('sign toggle for phone keypads and one-line headlines', () => {
  assert.equal(c.toggleSign('6.5'), '-6.5'); assert.equal(c.toggleSign('-6.5'), '+6.5'); assert.equal(c.toggleSign('+130'), '-130')
  assert.equal(c.toggleSign(''), '-'); assert.equal(c.toggleSign('\u2212110'), '+110'); assert.equal(c.toggleSign('PK'), 'PK'); assert.equal(c.toggleSign('0'), '0')
  assert.equal(c.headlineSpread('Florida', 12.9, -6.5), 'Model is 6.4 points more favourable to Florida')
  assert.equal(c.headlineSpread('Vanderbilt', -12.9, 6.5), 'Model is 6.4 points less favourable to Vanderbilt')
  assert.equal(c.headlineSpread('A', 7, -7), 'Model matches the spread for A')
  assert.equal(c.headlineSpread('A', 2, -1), 'Model is 1.0 point more favourable to A')
  assert.equal(c.headlineProbability('Florida', 0.839, 0.565), 'Model gives Florida 27.4 percentage points more win chance')
  assert.equal(c.headlineProbability('A', 0.4, 0.6), 'Model gives A 20.0 percentage points less win chance')
  assert.equal(c.headlineProbability('A', 0.6, 0.6), 'Model matches the market for A')
  assert.match(c.spreadExample('Florida'), /Florida −7 means Florida is favoured by 7/)
})

console.log(JSON.stringify({status: 'PASS', cases: results.length, results}, null, 2))
