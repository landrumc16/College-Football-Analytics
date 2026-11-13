import ProgramReportCard, { ReportCardExplorer, useReportCards } from './ProgramReportCard'
import HistoricalGameCoverage from './HistoricalGameCoverage'
import HistoricalResults from './HistoricalResults'
import { useEffect, useState } from 'react'
import { isPublishedHistoricalIntelligence } from './historicalPublication'
import { recentForm, trackedWinsAboveExpected, winsVsCurrentTop25, seasonFormTrend } from './programMetrics'

type WindowScore = { rank: number | null; strength: number | null; seasons_available: number; seasons_required: number; years?: number[]; sources?: { season: number; source: string }[] }
type Program = { season_strength_history?: { season: number; strength: number; source: string }[]; team: string; program_rankings: Record<string, WindowScore> | null; trajectory: { long_term: { classification: string }; medium_term?: { classification: string }; recent: { classification: string } } | null; hype: Record<string, { historical_tendency: string; dropped_out: number; entered_top25: number; seasons_observed: number; preseason_top25: number }> }
function combinedInsight(program: Program, poll: 'AP' | 'Coaches'): string {
  const hype = program.hype[poll]?.historical_tendency
  const trajectory = program.trajectory?.recent.classification
  const expectation = hype === 'historically_underhyped' ? 'underhyped' : hype === 'historically_overhyped' ? 'overhyped' : null
  const movement = trajectory === 'rapidly_rising' || trajectory === 'steadily_improving' ? 'rising'
    : trajectory === 'rapidly_declining' || trajectory === 'steadily_declining' ? 'declining' : null
  if (!expectation || !movement) return 'Insufficient evidence'
  return expectation === 'underhyped' && movement === 'rising' ? 'Overlooked improvement'
    : expectation === 'overhyped' && movement === 'declining' ? 'Reputation may mask decline'
    : expectation === 'overhyped' && movement === 'rising' ? 'Improving; expectations may run ahead'
    : 'Declining; expectations may be too negative'
}
function StrengthChart({ program }: { program: Program }) {
  const rows = (program.season_strength_history || []).filter(r => Number.isInteger(r.season) && Number.isFinite(r.strength) && !!r.source).sort((a, b) => a.season - b.season)
  if (rows.length < 2) return <p role="status">No verified season-by-season strength chart is available for this program.</p>
  const first = rows[0].season
  const last = rows[rows.length - 1].season
  const min = Math.min(...rows.map(r => r.strength))
  const max = Math.max(...rows.map(r => r.strength))
  const x = (season: number) => 40 + 440 * (season - first) / Math.max(1, last - first)
  const y = (strength: number) => 160 - 125 * (strength - min) / Math.max(1, max - min)
  // Separate runs at missing seasons; no connecting lines across data gaps.
  const segments: typeof rows[] = []
  rows.forEach(row => {
    if (!segments.length || row.season !== segments[segments.length - 1][segments[segments.length - 1].length - 1].season + 1) segments.push([])
    segments[segments.length - 1].push(row)
  })
  return <figure><svg role="img" aria-label={`Verified season strength history for ${program.team}`} viewBox="0 0 520 200" style={{ width: '100%', maxWidth: 720, height: 'auto' }}>
    <line x1="40" y1="165" x2="490" y2="165" stroke="currentColor" opacity=".5"/>
    {segments.map((segment, i) => <polyline key={i} fill="none" stroke="currentColor" strokeWidth="2.5" points={segment.map(row => `${x(row.season)},${y(row.strength)}`).join(' ')} />)}
    {rows.map(row => <circle key={row.season} cx={x(row.season)} cy={y(row.strength)} r="4" fill="currentColor"><title>{`${row.season}: strength ${row.strength.toFixed(2)} · ${row.source}`}</title></circle>)}
    <text x="40" y="190" fill="currentColor" fontSize="13">{first}</text><text x="480" y="190" textAnchor="end" fill="currentColor" fontSize="13">{last}</text>
    <text x="45" y="20" fill="currentColor" fontSize="12">Strength {max.toFixed(1)}</text>
    <text x="45" y="155" fill="currentColor" fontSize="12">{min.toFixed(1)}</text>
  </svg><figcaption>Verified schedule-adjusted strength by completed season. Gaps indicate missing data; higher means stronger, not a predicted finish.</figcaption></figure>
}
type CurrentPoll = { season: number; week: number; source: string; ap_top25: { team: string; rank: number }[]; coaches_top25: { team: string; rank: number }[] }
type CurrentRanking = { team: string; rank: number; rating?: number; wins?: number; losses?: number; projected_wins?: number }
type CompletedGame = { week: number; home: string; away: string; completed: boolean; home_score: number | null; away_score: number | null }
type TeamPerformance = { actual_wins: number; expected_wins: number; games_with_forecasts: number; wins_above_expected: number | null }
type Postseason = { team: string; cfp_field: number; national_title: number }
type ConferenceStanding = { team: string; conference_wins: number; conference_losses: number; conference_title_odds: number }
type Payload = { schema_version: number; status: string; latest_completed_season: number; programs: Program[] }

export default function ProgramIntelligence({ onTeam, onCompare, view = 'rankings', teams = [], currentPoll = null, currentRankings = [], currentSeason, conferenceTeams = {}, conferenceStandings = {}, schedule = [], performance = {}, postseason = [] }: { onTeam: (team: string) => void; onCompare?: (team: string) => void; teams?: string[]; currentPoll?: CurrentPoll | null; currentRankings?: CurrentRanking[]; currentSeason?: number; conferenceTeams?: Record<string, string[]>; conferenceStandings?: Record<string, ConferenceStanding[]>; schedule?: CompletedGame[]; performance?: Record<string, TeamPerformance>; postseason?: Postseason[]; view?: 'rankings' | 'hype' | 'trajectory' | 'stock' | 'contenders' | 'overview' }) {
  const verifiedCards = useReportCards()
  const [data, setData] = useState<Payload | null>(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [poll, setPoll] = useState<'AP' | 'Coaches'>('AP')
  const [conference, setConference] = useState('all')
  const [direction, setDirection] = useState('all')
  const [hypeOrder, setHypeOrder] = useState('dropouts')
  const [perceptionOrder, setPerceptionOrder] = useState<'poll' | 'disagreement'>('poll')
  const [perceptionConference, setPerceptionConference] = useState('all')
  const [chartTeam, setChartTeam] = useState('')
  const [window, setWindow] = useState<'10' | '5' | '3'>('10')
  useEffect(() => {
    if (view === 'stock' || view === 'contenders') return
    // Each historical view must not inherit a previous request's stale error.
    setError('')
    setData(null)
    let active = true
    fetch(import.meta.env.BASE_URL + 'v4-program-intelligence.json', { cache: 'no-store' })
      .then(response => { if (!response.ok || !response.headers.get('content-type')?.includes('json')) throw new Error('Verified historical program data has not been published yet.'); return response.json() })
      .then((payload: Payload) => {
        if (active) {
          if (!isPublishedHistoricalIntelligence(payload)) throw new Error('Historical research is awaiting independent source review.')
          setData(payload)
        }
      })
      .catch(e => { if (active) setError(String(e.message || e)) })
    return () => { active = false }
  }, [view])
  const programs = (data?.programs || []).filter(p => conference === 'all' || (conferenceTeams[conference] || []).includes(p.team)).filter(p => p.team.toLowerCase().includes(query.trim().toLowerCase()))
    .filter(p => view !== 'trajectory' || direction === 'all' || (p.trajectory?.recent.classification || 'insufficient_data') === direction)
    .sort((a, b) => {
      if (view === 'hype') {
        const metric = hypeOrder === 'entries' ? 'entered_top25' : hypeOrder === 'preseason' ? 'preseason_top25' : 'dropped_out'
        return (b.hype[poll]?.[metric] ?? -1) - (a.hype[poll]?.[metric] ?? -1) || a.team.localeCompare(b.team)
      }
      if (view === 'trajectory') return (a.program_rankings?.[window]?.rank ?? Infinity) - (b.program_rankings?.[window]?.rank ?? Infinity) || a.team.localeCompare(b.team)
      return (a.program_rankings?.[window]?.rank ?? Infinity) - (b.program_rankings?.[window]?.rank ?? Infinity) || a.team.localeCompare(b.team)
    })
  // Bound initial table length on narrow screens; filtering and sorting still apply to the full dataset.
  const [showAll, setShowAll] = useState(false)
  const [overviewOrder, setOverviewOrder] = useState<'rank' | 'recent' | 'expectations' | 'cfp'>('rank')
  const visiblePrograms = showAll ? programs : programs.slice(0, 25)
  const morePrograms = programs.length > 25
  const discoverableTeams = [...new Set(teams)].filter(team => team.toLowerCase().includes(query.trim().toLowerCase())).sort((a, b) => a.localeCompare(b))
  if (view === 'overview' || view === 'stock' || view === 'contenders') {
    const current = currentRankings.filter(team => Number.isFinite(team.rank) && team.rank > 0)
      .filter(team => team.team.toLowerCase().includes(query.trim().toLowerCase()))
      .filter(team => conference === 'all' || (conferenceTeams[conference] || []).includes(team.team))
      .sort((a, b) => {
        if (overviewOrder === 'recent') {
          const x = recentForm(schedule, a.team), y = recentForm(schedule, b.team)
          return (y.count ? y.wins / y.count : -1) - (x.count ? x.wins / x.count : -1) || a.rank - b.rank
        }
        if (overviewOrder === 'expectations') return (trackedWinsAboveExpected(performance[b.team]) ?? -Infinity) - (trackedWinsAboveExpected(performance[a.team]) ?? -Infinity) || a.rank - b.rank
        if (overviewOrder === 'cfp') return (postseason.find(p => p.team === b.team)?.cfp_field ?? -1) - (postseason.find(p => p.team === a.team)?.cfp_field ?? -1) || a.rank - b.rank
        return a.rank - b.rank
      })
    const visible = showAll ? current : current.slice(0, 10)
    return <section className="notice">
      <h2>{view === 'stock' ? 'Team Stock Watch' : view === 'contenders' ? 'Contenders & Pretenders' : 'Program Intelligence'}</h2>{query.trim() && currentRankings.some(r => r.team === query.trim()) ? <ProgramReportCard team={query.trim()} /> : null}
      <p>Three useful questions: how strong is a program now, is it improving, and is it meeting expectations? The published incumbent model provides current team strength. Multiweek momentum and historical expectations are shown only when verified records exist.</p>
      <details className="accuracy-summary"><summary>How to read these comparisons</summary>
        <p><strong>Strength:</strong> current published model ranking and rating, not a historical program ranking or a guarantee of future wins.</p>
        <p><strong>Recent form:</strong> wins and losses across the last five completed games with scores. Season trend compares wins in the most recent four scored games against the preceding four; a two-win difference indicates improving or declining form. It requires eight games and is not a change in team strength or a multi-season trajectory.</p>
        <p><strong>Expectations:</strong> verified current AP/Coaches Poll rank can be compared with the model. Disagreement is not proof that either ranking is wrong.</p>
      </details>
      <label>Find a program <input aria-label="Find a program" list="program-intelligence-teams" placeholder="Search programs…" value={query} onChange={e => setQuery(e.target.value)} /><datalist id="program-intelligence-teams">{currentRankings.map(team => <option key={team.team} value={team.team} />)}</datalist></label>
      <label>Conference <select aria-label="Filter programs by conference" value={conference} onChange={e => setConference(e.target.value)}><option value="all">All conferences</option>{Object.keys(conferenceTeams).sort().map(name => <option key={name} value={name}>{name}</option>)}</select></label>
      <label>Sort by <select aria-label="Sort program intelligence" value={overviewOrder} onChange={e => setOverviewOrder(e.target.value as typeof overviewOrder)}><option value="rank">Model ranking</option><option value="recent">Recent win rate</option><option value="expectations">Wins above tracked forecasts</option><option value="cfp">CFP probability</option></select></label>
      <div className="table-wrap program-intelligence-table"><table><thead><tr><th>Program</th><th>Model rank</th><th>Rating</th><th>Record</th><th>Conf. record</th><th>Top 25 wins</th><th>Last 5</th><th>Season trend</th><th>Vs forecast</th><th>AP Poll</th><th>Coaches Poll</th><th>CFP chance</th>{data && <th>3-year direction</th>}<th>Team</th></tr></thead><tbody>{visible.map(team => {
        const ap = currentPoll && currentPoll.season === currentSeason ? currentPoll.ap_top25.find(p => p.team === team.team)?.rank : undefined
        const coaches = currentPoll && currentPoll.season === currentSeason ? currentPoll.coaches_top25.find(p => p.team === team.team)?.rank : undefined
        const standing = Object.values(conferenceStandings).flat().find(s => s.team === team.team)
        const form = recentForm(schedule, team.team)
        const seasonTrend = seasonFormTrend(schedule, team.team)
        const forecastGap = trackedWinsAboveExpected(performance[team.team])
        const odds = postseason.find(p => p.team === team.team)?.cfp_field
        const direction = data?.programs.find(p => p.team === team.team)?.trajectory?.recent?.classification
        return <tr key={team.team}><td>{team.team}</td><td>#{team.rank}</td><td>{team.rating != null && Number.isFinite(team.rating) ? team.rating.toFixed(1) : '—'}</td><td>{team.wins != null && team.losses != null ? `${team.wins}–${team.losses}` : '—'}</td><td>{standing && Number.isFinite(standing.conference_wins) && Number.isFinite(standing.conference_losses) ? `${standing.conference_wins}–${standing.conference_losses}` : '—'}</td><td>{schedule.some(g => g.completed && (g.home === team.team || g.away === team.team) && g.home_score != null && g.away_score != null) ? winsVsCurrentTop25(schedule, team.team, currentRankings) : '—'}</td><td>{form.count ? `${form.wins}–${form.losses} (${form.count} games)` : '—'}</td><td>{seasonTrend ?? '—'}</td><td>{forecastGap != null ? `${forecastGap > 0 ? '+' : ''}${forecastGap.toFixed(1)} wins` : '—'}</td><td>{ap == null ? '—' : `#${ap}`}</td><td>{coaches == null ? '—' : `#${coaches}`}</td><td>{odds != null && Number.isFinite(odds) && odds >= 0 && odds <= 1 ? `${(odds * 100).toFixed(0)}%` : '—'}</td>{data && <td>{direction && direction !== 'insufficient_data' ? direction.replaceAll('_', ' ') : '—'}</td>}<td><button type="button" onClick={() => onTeam(team.team)}>View team</button>{onCompare && <> <button type="button" onClick={() => onCompare(team.team)} aria-label={`Compare ${team.team} with another school`}>Compare</button></>}</td></tr>
      })}</tbody></table></div>
      {data && <details className="accuracy-summary">
        <summary>Verified historical program development</summary>
        <p>Explore published season-by-season strength without substituting missing seasons. This chart is historical, not a current-season momentum forecast.</p>
        <label>Program history <select aria-label="Choose historical program" value={chartTeam} onChange={e => setChartTeam(e.target.value)}>
          <option value="">Choose a program</option>
          {data.programs.filter(p => (p.season_strength_history || []).length >= 2).sort((a,b) => a.team.localeCompare(b.team)).map(p => <option key={p.team} value={p.team}>{p.team}</option>)}
        </select></label>
        {chartTeam && data.programs.some(p => p.team === chartTeam) && <StrengthChart program={data.programs.find(p => p.team === chartTeam)!} />}
      </details>}
      {current.length > 10 && <p><button type="button" onClick={() => setShowAll(value => !value)}>{showAll ? 'Show top 10' : `Show all ${current.length} programs`}</button></p>}
      {!current.length && <p role="status">No published current-season rankings match this search.</p>}
      <p><small>Top 25 wins count victories against opponents in the current model Top 25, not their ranking at kickoff. AP and Coaches Poll columns are current polls, not preseason expectations.</small></p>
      <p role="status"><small>{data || verifiedCards ? 'Reviewed historical program research is available for eligible schools.' : 'Multi-season direction is shown only when independently reviewed historical research is published.'}</small></p>
      <p><small>Recent form is computed from completed games; forecast differences use the existing tracked prediction archive, not retrospective guesses. CFP percentages are published model projections, not guarantees. No synthetic stock scores, contender labels, or historical trends are inferred.</small></p>
    </section>
  }
  return <section className="notice">
    <h2>{view === 'hype' ? 'Historical Hype Index' : view === 'trajectory' ? 'Program Trajectory & Momentum' : 'Historical Program Rankings'}</h2>
    {view === 'hype' && <p><strong>Expectations vs. reality:</strong> Which programs repeatedly exceed or fall short of preseason poll expectations? Historical AP and Coaches evidence is kept separate from current-season model-versus-poll disagreement. This is not a forecast.</p>}
    {view === 'trajectory' && <p><strong>Program development:</strong> Are on-field results improving over several seasons? Win-rate levels and direction are different measures. Poll popularity does not determine trajectory.</p>}
    <p>{view === 'trajectory' ? 'Compare 3/5/10-year win rates and their annual trends from corroborated season results. Missing verified coverage is not inferred.' : view === 'hype' ? 'Compare preseason AP and Coaches expectations with final Top 25 results. Unranked is a capped boundary in the numeric index, never an asserted poll rank. Historical tendency requires all ten seasons.' : 'Opponent-adjusted historical strength, not current-season power rankings. A rank is only shown when all seasons in the selected window have verified coverage.'}</p>
    {verifiedCards && <ReportCardExplorer report={verifiedCards} onTeam={onTeam} conferenceTeams={conferenceTeams} view={view} />}
    {view === 'hype' && <details className="research-topic"><summary>Current-season poll disagreement</summary><section className="accuracy-summary" aria-label="Current-season poll perception"><h3>Current-season poll perception vs. Our Model</h3><label>Poll <select aria-label="Choose AP or Coaches Poll" value={poll} onChange={e => setPoll(e.target.value as 'AP' | 'Coaches')}><option value="AP">AP Poll</option><option value="Coaches">Coaches Poll</option></select></label><p>Poll rank minus model rank measures disagreement, not proven error: a positive difference means our model rates the school higher; a negative difference means the poll rates it higher. Rankings reflect different methods and may have different publication dates.</p>{currentPoll && currentPoll.season === currentSeason ? <><p>Season {currentPoll.season} · Poll week {currentPoll.week} · {currentPoll.source}</p><label>Order <select aria-label="Sort current poll perception" value={perceptionOrder} onChange={e => setPerceptionOrder(e.target.value as 'poll' | 'disagreement')}><option value="poll">Poll rank</option><option value="disagreement">Largest absolute disagreement</option></select></label><label>Conference <select aria-label="Filter current poll perception by conference" value={perceptionConference} onChange={e => setPerceptionConference(e.target.value)}><option value="all">All conferences</option>{Object.keys(conferenceTeams).sort().map(name => <option key={name} value={name}>{name}</option>)}</select></label><div className="table-wrap"><table><thead><tr><th>School</th><th>Our Model</th><th>{poll} Poll</th><th>Poll − Model</th></tr></thead><tbody>{(poll === 'AP' ? currentPoll.ap_top25 : currentPoll.coaches_top25).filter(entry => perceptionConference === 'all' || (conferenceTeams[perceptionConference] || []).includes(entry.team)).map(entry => { const model = currentRankings.find(row => row.team === entry.team)?.rank; return { ...entry, model, difference: model == null ? null : entry.rank - model } }).sort((a, b) => perceptionOrder === 'disagreement' ? (b.difference == null ? -1 : Math.abs(b.difference)) - (a.difference == null ? -1 : Math.abs(a.difference)) || a.rank - b.rank : a.rank - b.rank).map(entry => <tr key={entry.team}><td><button type="button" onClick={() => onTeam(entry.team)}>{entry.team}</button></td><td>{entry.model ?? '—'}</td><td>{entry.rank}</td><td>{entry.difference == null ? 'Unmatched' : entry.difference > 0 ? `+${entry.difference}` : entry.difference}</td></tr>)}</tbody></table></div><small>Only verified Top 25 poll entries are shown. Unmatched school names are not inferred; this comparison is independent of the historical Hype Index.</small></> : <p role="status">Current-season poll comparison is unavailable without a verified poll snapshot for this season.</p>}</section></details>}
    <details className="research-topic"><summary>Historical FBS results and coverage</summary><HistoricalResults onTeam={onTeam} /></details>
    {!verifiedCards && <HistoricalGameCoverage onTeam={onTeam} />}
    {error && !verifiedCards && <p role="status">{error} No rankings are estimated from missing data.</p>}
    {!data && !verifiedCards && !error && <p role="status">Checking independently reviewed historical research…</p>}
    {data && !verifiedCards && <><p>Through the {data.latest_completed_season} completed season · Descriptive research only</p>
      {view === 'trajectory' ? <><label>Momentum <select aria-label="Filter trajectory momentum" value={direction} onChange={e => setDirection(e.target.value)}><option value="all">All programs</option><option value="rapidly_rising">Rapidly rising</option><option value="steadily_improving">Steadily improving</option><option value="stable">Stable</option><option value="steadily_declining">Steadily declining</option><option value="rapidly_declining">Rapidly declining</option><option value="insufficient_data">Insufficient data</option></select></label><label>Strength window <select aria-label="Trajectory strength window" value={window} onChange={e => setWindow(e.target.value as '10' | '5' | '3')}><option value="10">10 seasons</option><option value="5">5 seasons</option><option value="3">3 seasons</option></select></label></> : view === 'hype' ? <><label>Explore <select aria-label="Sort historical hype" value={hypeOrder} onChange={e => setHypeOrder(e.target.value)}><option value="dropouts">Most preseason Top 25 dropouts</option><option value="entries">Most unranked-to-Top-25 entries</option><option value="preseason">Most preseason Top 25 appearances</option></select></label></> : <label>Ranking window <select value={window} onChange={e => setWindow(e.target.value as '10' | '5' | '3')}><option value="10">10 seasons</option><option value="5">5 seasons</option><option value="3">3 seasons</option></select></label>}
      <label>Conference <select aria-label="Filter historical programs by conference" value={conference} onChange={e => setConference(e.target.value)}><option value="all">All conferences</option>{Object.keys(conferenceTeams).sort().map(name => <option key={name} value={name}>{name}</option>)}</select></label>
      <input aria-label="Search historical programs" placeholder="Search programs…" value={query} onChange={e => setQuery(e.target.value)} />{query.trim() && programs.some(p => p.team === query.trim()) && <ProgramReportCard team={query.trim()} />}
      {view === 'trajectory' && data && <section className="accuracy-summary"><h3>Program strength history</h3><label>Chart program <select aria-label="Chart program strength" value={chartTeam} onChange={e => setChartTeam(e.target.value)}><option value="">Select a program</option>{programs.map(p => <option key={p.team} value={p.team}>{p.team}</option>)}</select></label>{chartTeam && <StrengthChart program={data.programs.find(p => p.team === chartTeam) || { team: chartTeam, program_rankings: null, trajectory: null, hype: {} }} />}</section>}
      {view === 'trajectory' && <p>Combined interpretations use only independently classified historical poll expectations and verified recent strength momentum. They are descriptive context, not an additional score or a forecast.</p>}
      {view === 'trajectory' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>10-year trajectory</th><th>5-year direction</th><th>3-year momentum</th><th>10-year rank</th><th>5-year rank</th><th>3-year rank</th><th>AP + trajectory</th><th>Coaches + trajectory</th></tr></thead><tbody>{visiblePrograms.map(p => <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.trajectory?.medium_term?.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.program_rankings?.['10']?.rank ?? '—'}</td><td>{p.program_rankings?.['5']?.rank ?? '—'}</td><td>{p.program_rankings?.['3']?.rank ?? '—'}</td><td>{combinedInsight(p, 'AP')}</td><td>{combinedInsight(p, 'Coaches')}</td></tr>)}</tbody></table></div> : view === 'hype' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>Historical tendency</th><th>Seasons</th><th>Preseason Top 25</th><th>Dropped out</th><th>Entered Top 25</th></tr></thead><tbody>{visiblePrograms.map(p => { const h = p.hype[poll]; return <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{h?.historical_tendency.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{h?.seasons_observed ?? '—'} / 10</td><td>{h?.preseason_top25 ?? '—'}</td><td>{h?.dropped_out ?? '—'}</td><td>{h?.entered_top25 ?? '—'}</td></tr> })}</tbody></table></div> : <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Program</th><th>Strength</th><th>Verified seasons</th><th>Source details</th><th>10-year trajectory</th><th>3-year momentum</th><th>AP hype</th><th>Coaches hype</th></tr></thead><tbody>{visiblePrograms.map(p => {
        const score = p.program_rankings?.[window]
        return <tr key={p.team}><td>{score?.rank ?? '—'}</td><td className="team"><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{score?.strength == null ? 'Insufficient data' : score.strength.toFixed(2)}</td><td>{score ? `${score.seasons_available}/${score.seasons_required}` : 'Unavailable'}</td><td>{score?.sources?.length ? <details><summary>{score.sources.length} sources</summary><ul>{score.sources.map(entry => <li key={entry.season}>{entry.season}: {entry.source}</li>)}</ul></details> : 'Not published'}</td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || '—'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || '—'}</td><td>{p.hype.AP?.historical_tendency.replaceAll('_', ' ') || '—'}</td><td>{p.hype.Coaches?.historical_tendency.replaceAll('_', ' ') || '—'}</td></tr>
      })}</tbody></table></div>}
      {view === 'rankings' && <p>Only complete, independently reviewed historical windows receive a rank. Coverage shows available seasons versus required seasons; a missing rank is not a zero score.</p>}
      {morePrograms && <p><button type="button" onClick={() => setShowAll(value => !value)} aria-label={showAll ? 'Show first 25 historical programs' : 'Show all historical programs'}>{showAll ? 'Show first 25 programs' : `Show all ${programs.length} programs`}</button> <small>{showAll ? 'All matching programs shown.' : `Showing the first 25 of ${programs.length} matching programs.`}</small></p>}
      {!programs.length && <p>No programs match this search.</p>}
    </>}
  </section>
}
