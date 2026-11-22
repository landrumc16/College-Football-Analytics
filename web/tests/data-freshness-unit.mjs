// Per-area freshness: each area keeps its own timestamp and an honest state (current, delayed, awaiting, unavailable).
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import vm from 'node:vm'
import ts from 'typescript'
const m = { exports: {} }
vm.runInNewContext(ts.transpileModule(await readFile('web/src/dataFreshness.ts', 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: m.exports, Date, Math, Number, Object, String })
const f = m.exports.freshness
const polls = { poll_weeks: { ap_top25: 12, coaches_top25: 12 }, ap_published_at: '2026-11-16', coaches_published_at: '2026-11-15', cfp_published_at: '2026-11-10', cfp_week: 11 }
const report = { retrieved_at: '2026-11-22T18:34:29Z', generated_at: '2026-11-22T18:35:00Z', data_freshness: { retrieved_at: '2026-11-22T18:34:29Z' } }
const by = items => Object.fromEntries(items.map(i => [i.area, i]))
const results = []

// Sunday afternoon: scores current; polls week 12; the Nov 17 CFP release is due but unverified.
let s = by(f(report, polls, new Date('2026-11-22T20:00:00Z')))
assert.equal(s['Scores and records'].state, 'current')
assert.equal(s['AP Poll'].text, 'week 12, published Nov 16')
assert.equal(s['CFP rankings'].state, 'awaiting'); assert.match(s['CFP rankings'].text, /Nov 10 release shown; Nov 17 release awaiting verification/)
results.push('Sunday: per-area states, CFP awaiting verification')

// Before the Nov 17 release time the Nov 10 release is current and verified.
s = by(f(report, polls, new Date('2026-11-17T20:00:00Z')))
assert.equal(s['CFP rankings'].state, 'current'); assert.match(s['CFP rankings'].text, /Nov 10 release \(verified\)/)
results.push('CFP current between releases')

// Scores older than the daily baseline plus margin are labelled delayed, not current.
s = by(f(report, polls, new Date('2026-11-24T00:00:00Z')))
assert.equal(s['Scores and records'].state, 'delayed'); assert.match(s['Scores and records'].text, /update delayed/)
results.push('stale scores flagged as delayed')

// Missing inputs are unavailable, never invented.
s = by(f({}, null, new Date('2026-11-01T00:00:00Z')))
assert.equal(s['Scores and records'].state, 'unavailable'); assert.equal(s['AP Poll'].text, 'not yet published'); assert.equal(s['CFP rankings'].state, 'unavailable')
assert.equal(f(report, polls, new Date()).length, 5)
results.push('missing data unavailable; five independent areas')
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
