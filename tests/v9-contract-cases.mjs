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
