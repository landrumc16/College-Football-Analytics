import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { pathToFileURL } from 'node:url'
import ts from 'typescript'

const source = await readFile('web/src/historicalPublication.ts', 'utf8')
const js = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
const { isPublishedHistoricalIntelligence: accepts } = await import('data:text/javascript,' + encodeURIComponent(js))

const good = {
  schema_version: 1,
  status: 'descriptive_only',
  source_review_attested: true,
  predictive_validation: false,
  latest_completed_season: 2025,
  provenance_diagnostics: {
    status: 'provenance_format_checked_not_independently_verified',
    required_window: [2016, 2025],
    strength_programs_full_window: 1,
    poll_programs_full_window: 1
  },
  programs: [{ team: 'Example', program_rankings: {}, hype: {} }]
}
assert.equal(accepts(good), true, 'source-attested payload with full coverage should be accepted')
for (const [name, mutate] of [
  ['missing attestation', p => { delete p.source_review_attested }],
  ['wrong season window', p => { p.provenance_diagnostics.required_window[0] = 2017 }],
  ['no poll coverage', p => { p.provenance_diagnostics.poll_programs_full_window = 0 }],
  ['fractional strength coverage', p => { p.provenance_diagnostics.strength_programs_full_window = 1.5 }],
  ['missing provenance', p => { delete p.provenance_diagnostics }],
  ['empty programs', p => { p.programs = [] }],
  ['duplicate programs', p => { p.programs.push({ ...p.programs[0] }) }],
  ['missing team name', p => { p.programs[0].team = '' }],
  ['future latest season mismatch', p => { p.latest_completed_season = 2026 }],
  ['predictive validation claim', p => { p.predictive_validation = true }]
]) {
  const candidate = structuredClone(good)
  mutate(candidate)
  assert.equal(accepts(candidate), false, name)
}
console.log('Historical publication gate: valid and 10 invalid fixtures passed')

// The approved V5 Report Card contract is separate from abandoned V4
// cross-season strength research. Its real publication must also fail closed.
const cardsSource = (await readFile('web/src/ProgramReportCard.tsx', 'utf8')).replace(/^import .*from 'react'\s*$/m, '')
const cardsJs = ts.transpileModule(cardsSource, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.React } }).outputText
const { validReportCards } = await import('data:text/javascript,' + encodeURIComponent(cardsJs))
const cards = JSON.parse(await readFile('web/public/v5-program-report-cards.json', 'utf8'))
assert.equal(validReportCards(cards), true, 'actual independently reviewed V5 publication')
for (const [name, mutate] of [
  ['missing source review', p => { delete p.source_review }],
  ['unreviewed polls', p => { p.source_review.polls = false }],
  ['unreviewed results', p => { p.source_review.historical_results = false }],
  ['unreviewed strength', p => { p.source_review.incumbent_strength = false }],
  ['insufficient peers', p => { p.coverage.hype.verified = 10 }],
  ['duplicate peers', p => { p.programs[1].team = p.programs[0].team }],
  ['missing sources', p => { p.sources = [] }],
  ['invented overall', p => { const r = p.programs.find(r => r.overall_score !== null); r.overall_score += 1 }],
  ['missing category reweighted', p => { p.programs.find(r => r.overall_score !== null).categories.hype = { score: null, grade: null } }]
]) {
  const candidate = structuredClone(cards)
  mutate(candidate)
  assert.equal(validReportCards(candidate), false, name)
}
console.log('V5 real national publication and 9 adversarial provenance/coverage/weight cases passed')
