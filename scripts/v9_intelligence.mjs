/** Offline intelligence publication using the released current-level calculation. */
import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { pathToFileURL } from 'node:url'
import { execFileSync } from 'node:child_process'

export function sourceAge(timestamp, now, maxAgeHours = 24) {
  if (!timestamp) return { status: 'missing', age_hours: null }
  if (!/(Z|[+-]\d\d:\d\d)$/.test(timestamp) || !Number.isFinite(Date.parse(timestamp))) return { status: 'invalid', age_hours: null }
  const age = (now - Date.parse(timestamp)) / 3600000
  return { status: age < 0 ? 'future' : age > maxAgeHours ? 'stale' : 'current', age_hours: age }
}

export function buildIntelligence(report, stats, strengthScores, now = Date.now()) {
  if (!Array.isArray(report.rankings) || !report.rankings.length) throw Error('Missing rankings')
  const ratings = Object.fromEntries(report.rankings.map(row => [row.team, row.rating]))
  if (Object.keys(ratings).length !== report.rankings.length) throw Error('Duplicate teams')
  const fields = stats?.fields ?? []
  const adjusted = fields.indexOf('adjusted'), sample = fields.indexOf('n')
  const receipt = report.retrieved_at ?? null
  const statReceipt = stats?.generated_at ?? null
  const period = { season: report.season, through: receipt }
  const wrap = (value, units, population, games, source, limitations = []) => ({
    value, units, population, sample: games, source, limitations,
    period: source === 'v8-team-stats.json' ? { season: report.season, through: statReceipt } : period,
    source_receipt: source === 'v8-team-stats.json' ? statReceipt : receipt,
    freshness: sourceAge(source === 'v8-team-stats.json' ? statReceipt : receipt, now),
    status: value === null ? 'unavailable' : 'available',
  })
  const teams = report.rankings.map(row => {
    if (!Number.isFinite(row.rating)) throw Error('Invalid season rating')
    const played = report.schedule.filter(g => g.completed && [g.home, g.away].includes(row.team))
    const level = strengthScores(row.team, row.rating, ratings, report.schedule)
    const unit = stats?.teams?.[row.team]
    const metrics = {}
    for (const side of ['offense', 'defense']) {
      const epa = unit?.[side]?.epa
      metrics[side] = wrap(adjusted >= 0 && Number.isFinite(epa?.[adjusted]) ? epa[adjusted] : null,
        'EPA/play', 'eligible FBS vs FBS', epa?.[sample] ?? null,
        'v8-team-stats.json', ['Approximate estimate uncertainty is not a future-score interval'])
    }
    const opponents = played.map(g => ratings[g.home === row.team ? g.away : g.home]).filter(Number.isFinite)
    const trends = Object.fromEntries(Object.entries(unit?.trend ?? {}).map(([key, trend]) => [key, {
      ...wrap(trend ?? null, 'opponent-adjusted game rate', 'eligible FBS games', trend?.games ?? null,
        'v8-team-stats.json', ['Last-four preferred; inherited last-three fallback', 'Descriptive approximate trend rule']),
      requested_window: 4, actual_window: trend?.games ?? null,
    }]))
    const team = {
      team: row.team,
      period: { season: report.season, through: receipt },
      accomplishment: { wins: row.wins, losses: row.losses, national_metric: null,
        status: 'record_available_metric_unvalidated', units: 'games', population: 'published team schedule', sample: played.length, source: 'season-report.json', source_receipt: receipt },
      strength: wrap(row.rating, 'rating points', 'published FBS teams', played.length, 'season-report.json'),
      current_level: { ...wrap(level?.momentum ?? null, 'rating points', 'latest completed team games',
        level?.momentumGames ?? 0, 'released strengthScores.ts', ['Current opponent ratings', 'Inherited neutral-site and FCS fallback semantics']), window: 3 },
      schedule: wrap(opponents.length ? opponents.reduce((a,b) => a+b,0)/opponents.length : null,
        'opponent rating points', 'played opponents with published ratings', opponents.length,
        'season-report.json', ['FCS and unrated opponents excluded from this summary', 'Current-knowledge context']),
      units: metrics, trends, consistency: wrap(unit?.volatility ?? null, 'SD of opponent-adjusted game values', 'eligible FBS games; minimum five', null, 'v8-team-stats.json', ['Sample sizes are retained per metric']),
      power_opponents: { games: unit?.power_games ?? null, definition: stats?.method?.power ?? null, source: 'v8-team-stats.json', population: 'season-specific power opponents', units: 'games', period: { season: report.season, through: statReceipt }, source_receipt: statReceipt },
      findings: [ {
        id: 'season-strength', rule_version: 1,
        takeaway: `${row.team} has a season strength rating of ${row.rating.toFixed(1)}.`,
        evidence_paths: ['strength.value'], source_receipt: receipt,
        explanation: 'The existing season rating summarizes the published model. Model rank also includes projected wins.',
      } ],
    }
    const finding = (id, takeaway, evidence_paths, source_receipt, explanation) => ({ id, rule_version: 1, takeaway, evidence_paths, source_receipt, explanation })
    team.findings.push(finding('earned-record', `${row.team} has earned ${row.wins} wins and ${row.losses} losses.`, ['accomplishment.wins', 'accomplishment.losses'], receipt, 'Observed results. An accomplishment national metric remains unvalidated.'))
    if (level?.momentum !== null && Number.isFinite(level?.momentum)) team.findings.push(finding('current-level', `Last-three playing level is ${level.momentum.toFixed(1)} versus season strength ${row.rating.toFixed(1)}.`, ['current_level.value','strength.value'], receipt, 'Uses the released three-game function and current opponent ratings. A short sample does not establish future improvement.'))
    for (const side of ['offense', 'defense']) {
      if (metrics[side].status === 'available') team.findings.push(finding(`${side}-efficiency`, `${side === 'offense' ? 'Offense generated' : 'Defense allowed'} ${metrics[side].value.toFixed(3)} opponent-adjusted EPA per play.`, [`units.${side}.value`], statReceipt, `Eligible FBS sample ${metrics[side].sample} plays. Lower allowed EPA is better on defense. Descriptive evidence does not identify a causal coaching or personnel effect.`))
    }
    if (team.schedule.status === 'available') team.findings.push(finding('schedule-context', `Rated opponents averaged ${team.schedule.value.toFixed(1)} strength points across ${opponents.length} completed games.`, ['schedule.value','schedule.sample'], receipt, 'Current-knowledge schedule context excludes unrated and FCS opponents and applies no extra conference multiplier.'))
    return team
  })
  return { schema_version: 1, season: report.season, model_metadata: report.model_metadata,
    sources: { report: receipt, statistics: stats?.generated_at ?? null, actual_publication_at: null, freshness: { report: sourceAge(receipt, now), statistics: sourceAge(statReceipt, now) }, missing_statistics: !stats?.teams },
    teams, history_semantics: 'retained observations; earlier snapshots unavailable' }
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const directory = process.argv[2]
  if (!directory) throw Error('Supply isolated output directory')
  if (path.resolve(directory).includes(path.resolve('web/public'))) throw Error('Use an isolated development output')
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'cfa-v9-'))
  try {
    execFileSync('web/node_modules/.bin/esbuild', ['web/src/strengthScores.ts', '--bundle', '--format=esm', `--outfile=${temporary}/strength.mjs`])
    const { strengthScores } = await import(pathToFileURL(`${temporary}/strength.mjs`))
    const report = JSON.parse(fs.readFileSync('data/season-2026-report.json'))
    const stats = JSON.parse(fs.readFileSync('web/public/v8-team-stats.json'))
    const intelligence = buildIntelligence(report, stats, strengthScores)
    fs.mkdirSync(directory, { recursive: true })
    const retained = 'docs/evidence/v9/strength-history'
    if (fs.existsSync(retained)) fs.cpSync(retained, `${directory}/strength-history`, { recursive: true })
    execFileSync('python', ['scripts/v9_strength_snapshot.py', '--report', 'data/season-2026-report.json',
      '--archive', `${directory}/strength-history`, '--source-commit', execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()])
    intelligence.observations = fs.readdirSync(`${directory}/strength-history`).filter(name => name.endsWith('.json')).map(name => JSON.parse(fs.readFileSync(`${directory}/strength-history/${name}`))).sort((a,b) => a.report_generated_at.localeCompare(b.report_generated_at))
    const output = `${directory}/team-intelligence.json`
    const staged = `${output}.${process.pid}.tmp`
    fs.writeFileSync(staged, JSON.stringify(intelligence, null, 2)+'\n')
    fs.renameSync(staged, output)
    console.log(`Published ${intelligence.teams.length} teams to ${directory}`)
  } finally { fs.rmSync(temporary, { recursive: true, force: true }) }
}
