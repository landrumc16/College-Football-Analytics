import assert from 'node:assert/strict'
import { buildIntelligence } from '../scripts/v9_intelligence.mjs'
const report = { season: 2026, rankings: [{team:'A', rating:1, wins:0, losses:0}], schedule: [] }
const strength = () => ({momentum:null,momentumGames:0})
const result = buildIntelligence(report, null, strength)
assert.equal(result.teams[0].units.offense.status, 'unavailable')
assert.equal(result.teams[0].current_level.value, null)
assert.equal(result.teams[0].schedule.value, null)
assert.equal(result.sources.actual_publication_at, null)
assert.throws(() => buildIntelligence({...report, rankings:[...report.rankings,...report.rankings]}, null, strength), /Duplicate/)
assert.throws(() => buildIntelligence({...report, rankings:[{team:'A',rating:NaN}]}, null, strength), /Invalid/)
console.log('Missing data, thin samples, duplicate and nonfinite input cases passed')
const { sourceAge } = await import('../scripts/v9_intelligence.mjs')
const now = Date.parse('2026-11-25T18:00:00Z')
for (const [stamp, status] of [[null,'missing'],['bad','invalid'],['2026-11-25T17:00:00','invalid'],['2026-11-25T19:00:00Z','future'],['2026-11-23T18:00:00Z','stale'],['2026-11-25T17:00:00Z','current']]) {
  assert.equal(sourceAge(stamp, now).status, status)
}
const missing = buildIntelligence(report, null, strength, now)
assert.equal(missing.teams[0].units.offense.freshness.status, 'missing')
for (const finding of missing.teams[0].findings) {
  for (const pointer of finding.evidence_paths) {
    assert.notEqual(pointer.split('.').reduce((value, key) => value?.[key], missing.teams[0]), undefined)
  }
}
console.log('Freshness boundaries and finding evidence paths passed')
