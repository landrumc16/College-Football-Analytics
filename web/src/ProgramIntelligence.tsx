import { useEffect, useState } from 'react'
import { isPublishedHistoricalIntelligence } from './historicalPublication'

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
type CurrentRanking = { team: string; rank: number }
type Payload = { schema_version: number; status: string; latest_completed_season: number; programs: Program[] }

export default function ProgramIntelligence({ onTeam, view = 'rankings', teams = [], currentPoll = null, currentRankings = [], currentSeason, conferenceTeams = {} }: { onTeam: (team: string) => void; teams?: string[]; currentPoll?: CurrentPoll | null; currentRankings?: CurrentRanking[]; currentSeason?: number; conferenceTeams?: Record<string, string[]>; view?: 'rankings' | 'hype' | 'trajectory' | 'stock' | 'contenders' }) {
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
      .then(response => { if (!response.ok) throw new Error('Verified historical program data has not been published yet.'); return response.json() })
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
  const discoverableTeams = [...new Set(teams)].filter(team => team.toLowerCase().includes(query.trim().toLowerCase())).sort((a, b) => a.localeCompare(b))
  if (view === 'stock' || view === 'contenders') return <section className="notice">
    <h2>{view === 'stock' ? 'Team Stock Watch' : 'Contenders & Pretenders'}</h2>
    <p>{view === 'stock'
      ? 'Four-week movement requires verified, dated weekly snapshots and a validated 0–100 stock formula. Current rankings and season totals are not substitutes.'
      : 'Independent classification requires a validated, schedule-adjusted expected-record model and sufficient as-of-date evidence. CFP odds and season-total forecast gaps are not substitutes.'}</p>
    <p role="status">{view === 'stock' ? 'Verified stock movement is unavailable.' : 'Independent contender classifications are unavailable.'} No scores or classifications have been inferred.</p>
    <label>Find a team <input aria-label="Find a team profile" placeholder="Search programs…" value={query} onChange={e => setQuery(e.target.value)} /></label>
    <p>Current-season programs are listed for navigation only; no unverified historical indicators are assigned.</p>
    <div className="table-wrap"><table><thead><tr><th>Program</th><th>{view === 'stock' ? 'Four-week movement' : 'Classification'}</th><th>Team details</th></tr></thead>
    <tbody>{discoverableTeams.map(team => <tr key={team}><td>{team}</td><td>{view === 'stock' ? 'Insufficient verified snapshots' : 'Too Early to Tell'}</td><td><button type="button" onClick={() => onTeam(team)}>View Team Profile</button></td></tr>)}</tbody></table></div>
    {!discoverableTeams.length && <p>No programs match this search.</p>}
  </section>
  return <section className="notice">
    <h2>{view === 'hype' ? 'Historical Hype Index' : view === 'trajectory' ? 'Program Trajectory & Momentum' : 'Historical Program Rankings'}</h2>
    {view === 'hype' && <p><strong>Expectations vs. reality:</strong> Which programs repeatedly exceed or fall short of preseason poll expectations? Historical AP and Coaches evidence is kept separate from current-season model-versus-poll disagreement. This is not a forecast.</p>}
    {view === 'trajectory' && <p><strong>Program development:</strong> Is on-field strength improving over several seasons, or was one season an outlier? Long-term strength and recent momentum are different measures. Poll popularity does not determine trajectory.</p>}
    <p>{view === 'trajectory' ? 'Compare ten-year direction and three-year momentum using the shared historical program research. Missing verified coverage is not inferred.' : view === 'hype' ? 'Compare preseason AP and Coaches expectations with final Top 25 results. Unranked is never treated as a fabricated rank 26. Historical tendency requires all ten seasons.' : 'Opponent-adjusted historical strength, not current-season power rankings. A rank is only shown when all seasons in the selected window have verified coverage.'}</p>
    {view === 'hype' && <section className="accuracy-summary" aria-label="Current-season poll perception"><h3>Current-season poll perception vs. Our Model</h3><label>Poll <select aria-label="Choose AP or Coaches Poll" value={poll} onChange={e => setPoll(e.target.value as 'AP' | 'Coaches')}><option value="AP">AP Poll</option><option value="Coaches">Coaches Poll</option></select></label><p>Poll rank minus model rank measures disagreement, not proven error: a positive difference means our model rates the school higher; a negative difference means the poll rates it higher. Rankings reflect different methods and may have different publication dates.</p>{currentPoll && currentPoll.season === currentSeason ? <><p>Season {currentPoll.season} · Poll week {currentPoll.week} · {currentPoll.source}</p><label>Order <select aria-label="Sort current poll perception" value={perceptionOrder} onChange={e => setPerceptionOrder(e.target.value as 'poll' | 'disagreement')}><option value="poll">Poll rank</option><option value="disagreement">Largest absolute disagreement</option></select></label><label>Conference <select aria-label="Filter current poll perception by conference" value={perceptionConference} onChange={e => setPerceptionConference(e.target.value)}><option value="all">All conferences</option>{Object.keys(conferenceTeams).sort().map(name => <option key={name} value={name}>{name}</option>)}</select></label><div className="table-wrap"><table><thead><tr><th>School</th><th>Our Model</th><th>{poll} Poll</th><th>Poll − Model</th></tr></thead><tbody>{(poll === 'AP' ? currentPoll.ap_top25 : currentPoll.coaches_top25).filter(entry => perceptionConference === 'all' || (conferenceTeams[perceptionConference] || []).includes(entry.team)).map(entry => { const model = currentRankings.find(row => row.team === entry.team)?.rank; return { ...entry, model, difference: model == null ? null : entry.rank - model } }).sort((a, b) => perceptionOrder === 'disagreement' ? (b.difference == null ? -1 : Math.abs(b.difference)) - (a.difference == null ? -1 : Math.abs(a.difference)) || a.rank - b.rank : a.rank - b.rank).map(entry => <tr key={entry.team}><td><button type="button" onClick={() => onTeam(entry.team)}>{entry.team}</button></td><td>{entry.model ?? '—'}</td><td>{entry.rank}</td><td>{entry.difference == null ? 'Unmatched' : entry.difference > 0 ? `+${entry.difference}` : entry.difference}</td></tr>)}</tbody></table></div><small>Only verified Top 25 poll entries are shown. Unmatched school names are not inferred; this comparison is independent of the historical Hype Index.</small></> : <p role="status">Current-season poll comparison is unavailable without a verified poll snapshot for this season.</p>}</section>}
    {error && <p role="status">{error} No rankings are estimated from missing data.</p>}
    {!data && !error && <p role="status">Checking independently reviewed historical research…</p>}
    {data && <><p>Through the {data.latest_completed_season} completed season · Descriptive research only</p>
      {view === 'trajectory' ? <><label>Momentum <select aria-label="Filter trajectory momentum" value={direction} onChange={e => setDirection(e.target.value)}><option value="all">All programs</option><option value="rapidly_rising">Rapidly rising</option><option value="steadily_improving">Steadily improving</option><option value="stable">Stable</option><option value="steadily_declining">Steadily declining</option><option value="rapidly_declining">Rapidly declining</option><option value="insufficient_data">Insufficient data</option></select></label><label>Strength window <select aria-label="Trajectory strength window" value={window} onChange={e => setWindow(e.target.value as '10' | '5' | '3')}><option value="10">10 seasons</option><option value="5">5 seasons</option><option value="3">3 seasons</option></select></label></> : view === 'hype' ? <><label>Explore <select aria-label="Sort historical hype" value={hypeOrder} onChange={e => setHypeOrder(e.target.value)}><option value="dropouts">Most preseason Top 25 dropouts</option><option value="entries">Most unranked-to-Top-25 entries</option><option value="preseason">Most preseason Top 25 appearances</option></select></label></> : <label>Ranking window <select value={window} onChange={e => setWindow(e.target.value as '10' | '5' | '3')}><option value="10">10 seasons</option><option value="5">5 seasons</option><option value="3">3 seasons</option></select></label>}
      <label>Conference <select aria-label="Filter historical programs by conference" value={conference} onChange={e => setConference(e.target.value)}><option value="all">All conferences</option>{Object.keys(conferenceTeams).sort().map(name => <option key={name} value={name}>{name}</option>)}</select></label>
      <input aria-label="Search historical programs" placeholder="Search programs…" value={query} onChange={e => setQuery(e.target.value)} />
      {view === 'trajectory' && data && <section className="accuracy-summary"><h3>Program strength history</h3><label>Chart program <select aria-label="Chart program strength" value={chartTeam} onChange={e => setChartTeam(e.target.value)}><option value="">Select a program</option>{programs.map(p => <option key={p.team} value={p.team}>{p.team}</option>)}</select></label>{chartTeam && <StrengthChart program={data.programs.find(p => p.team === chartTeam) || { team: chartTeam, program_rankings: null, trajectory: null, hype: {} }} />}</section>}
      {view === 'trajectory' && <p>Combined interpretations use only independently classified historical poll expectations and verified recent strength momentum. They are descriptive context, not an additional score or a forecast.</p>}
      {view === 'trajectory' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>10-year trajectory</th><th>5-year direction</th><th>3-year momentum</th><th>10-year rank</th><th>5-year rank</th><th>3-year rank</th><th>AP + trajectory</th><th>Coaches + trajectory</th></tr></thead><tbody>{programs.map(p => <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.trajectory?.medium_term?.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.program_rankings?.['10']?.rank ?? '—'}</td><td>{p.program_rankings?.['5']?.rank ?? '—'}</td><td>{p.program_rankings?.['3']?.rank ?? '—'}</td><td>{combinedInsight(p, 'AP')}</td><td>{combinedInsight(p, 'Coaches')}</td></tr>)}</tbody></table></div> : view === 'hype' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>Historical tendency</th><th>Seasons</th><th>Preseason Top 25</th><th>Dropped out</th><th>Entered Top 25</th></tr></thead><tbody>{programs.map(p => { const h = p.hype[poll]; return <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{h?.historical_tendency.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{h?.seasons_observed ?? '—'} / 10</td><td>{h?.preseason_top25 ?? '—'}</td><td>{h?.dropped_out ?? '—'}</td><td>{h?.entered_top25 ?? '—'}</td></tr> })}</tbody></table></div> : <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Program</th><th>Strength</th><th>Verified seasons</th><th>Source details</th><th>10-year trajectory</th><th>3-year momentum</th><th>AP hype</th><th>Coaches hype</th></tr></thead><tbody>{programs.map(p => {
        const score = p.program_rankings?.[window]
        return <tr key={p.team}><td>{score?.rank ?? '—'}</td><td className="team"><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{score?.strength == null ? 'Insufficient data' : score.strength.toFixed(2)}</td><td>{score ? `${score.seasons_available}/${score.seasons_required}` : 'Unavailable'}</td><td>{score?.sources?.length ? <details><summary>{score.sources.length} sources</summary><ul>{score.sources.map(entry => <li key={entry.season}>{entry.season}: {entry.source}</li>)}</ul></details> : 'Not published'}</td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || '—'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || '—'}</td><td>{p.hype.AP?.historical_tendency.replaceAll('_', ' ') || '—'}</td><td>{p.hype.Coaches?.historical_tendency.replaceAll('_', ' ') || '—'}</td></tr>
      })}</tbody></table></div>}
      {view === 'rankings' && <p>Only complete, independently reviewed historical windows receive a rank. Coverage shows available seasons versus required seasons; a missing rank is not a zero score.</p>}
      {!programs.length && <p>No programs match this search.</p>}
    </>}
  </section>
}
