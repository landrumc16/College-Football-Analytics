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
// The one-line summary names only the areas that need attention.
assert.equal(m.exports.statusSummary(f(report, polls, new Date('2026-11-22T20:00:00Z'))), 'CFP rankings awaiting verification')
assert.equal(m.exports.statusSummary(f(report, polls, new Date('2026-11-17T20:00:00Z'))), 'all current')
assert.equal(m.exports.statusSummary(f(report, polls, new Date('2026-11-24T00:00:00Z'))), 'Scores and records update delayed; CFP rankings awaiting verification')
results.push('one-line summary flags only areas needing attention')

// The 24 November incident: the release aired at 18:00 Central (00:00 UTC on the 25th). Fifteen minutes later the
// footer must stop saying "all current" (it previously waited until 06:00 UTC, six hours after the release).
const nov17 = { ...polls, cfp_published_at: '2026-11-17', cfp_week: 12 }
s = by(f(report, nov17, new Date('2026-11-25T00:10:00Z')))
assert.equal(s['CFP rankings'].state, 'current')
s = by(f(report, nov17, new Date('2026-11-25T00:16:00Z')))
assert.equal(s['CFP rankings'].state, 'awaiting'); assert.match(s['CFP rankings'].text, /Nov 24 release awaiting verification/)
assert.notEqual(m.exports.statusSummary(f(report, nov17, new Date('2026-11-25T00:16:00Z'))), 'all current')
// Selection day (Sunday 6 December) airs at 11:00 Central (17:00 UTC).
assert.equal(new Date(m.exports.cfpOverdueAt('2026-12-06')).toISOString(), '2026-12-06T17:15:00.000Z')
assert.equal(new Date(m.exports.cfpOverdueAt('2026-11-24')).toISOString(), '2026-11-25T00:15:00.000Z')
results.push('an aired CFP release is flagged 15 minutes after its scheduled time, not six hours')

// Deployed monitor status: active monitoring adds a current row; a stopped chain or a critical alert is never "all current".
const fresh = { ...report, retrieved_at: '2026-11-25T00:00:00Z', data_freshness: { retrieved_at: '2026-11-25T00:00:00Z' } }
const at = new Date('2026-11-25T01:00:00Z'), cfp24 = { ...polls, cfp_published_at: '2026-11-24', cfp_week: 13 }
const active = { watcher: { state: 'active', last_run_at: '2026-11-25T00:50:00Z' }, alerts: [] }
s = by(f(fresh, cfp24, at, active))
assert.equal(s['Live monitoring'].state, 'current'); assert.equal(m.exports.statusSummary(f(fresh, cfp24, at, active)), 'all current')
const stopped = { watcher: { state: 'stopped', last_run_at: '2026-11-24T19:51:00Z' }, alerts: [] }
s = by(f(fresh, cfp24, at, stopped))
assert.equal(s['Live monitoring'].state, 'delayed'); assert.match(s['Live monitoring'].text, /interrupted since/)
assert.equal(m.exports.statusSummary(f(fresh, cfp24, at, stopped)), 'Live monitoring interrupted')
const games = { watcher: { state: 'active' }, alerts: [
  { key: 'games-awaiting', area: 'Scores and records', severity: 'critical', text: '2 finished game(s) not yet published (A at B, C at D)' },
  { key: 'missed-schedule:refresh-data.yml', area: 'Scheduling', severity: 'warning', text: 'late cron' },
  { key: 'deploy-failed', area: 'Publishing', severity: 'critical', text: 'The latest site deployment failed' }] }
s = by(f(fresh, cfp24, at, games))
assert.equal(s['Scores and records'].state, 'delayed'); assert.match(s['Scores and records'].text, /not yet published/)
assert.equal(s['Publishing'].state, 'delayed'); assert.equal(s['Scheduling'], undefined)    // warnings stay in the issue
assert.equal(m.exports.statusSummary(f(fresh, cfp24, at, games)), 'Scores and records update delayed; Publishing update delayed')
// Unknown status (file missing or unreadable) adds nothing and claims nothing.
assert.equal(f(fresh, cfp24, at, undefined).length, 5)
assert.equal(f(fresh, cfp24, at, { alerts: [], watcher: { state: 'unknown' } }).length, 5)
results.push('monitor status: active/interrupted monitoring and critical alerts reflected; warnings and unknowns are not')
console.log(JSON.stringify({ status: 'PASS', cases: results.length, results }, null, 2))
