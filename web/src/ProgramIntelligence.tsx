import { useEffect, useState } from 'react'
import { isPublishedHistoricalIntelligence } from './historicalPublication'

type WindowScore = { rank: number | null; strength: number | null; seasons_available: number; seasons_required: number; years?: number[]; sources?: { season: number; source: string }[] }
type Program = { team: string; program_rankings: Record<string, WindowScore> | null; trajectory: { long_term: { classification: string }; recent: { classification: string } } | null; hype: Record<string, { historical_tendency: string; dropped_out: number; entered_top25: number; seasons_observed: number; preseason_top25: number }> }
type Payload = { schema_version: number; status: string; latest_completed_season: number; programs: Program[] }

export default function ProgramIntelligence({ onTeam, view = 'rankings', teams = [] }: { onTeam: (team: string) => void; teams?: string[]; view?: 'rankings' | 'hype' | 'trajectory' | 'stock' | 'contenders' }) {
  const [data, setData] = useState<Payload | null>(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [poll, setPoll] = useState<'AP' | 'Coaches'>('AP')
  const [window, setWindow] = useState<'10' | '5' | '3'>('10')
  useEffect(() => {
    if (view === 'stock' || view === 'contenders') return
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
  const programs = (data?.programs || []).filter(p => p.team.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => view === 'hype' ? (b.hype[poll]?.dropped_out ?? -1) - (a.hype[poll]?.dropped_out ?? -1) || a.team.localeCompare(b.team) : view === 'trajectory' ? (a.trajectory?.recent.classification || 'zz').localeCompare(b.trajectory?.recent.classification || 'zz') || a.team.localeCompare(b.team) : (a.program_rankings?.[window]?.rank ?? Infinity) - (b.program_rankings?.[window]?.rank ?? Infinity) || a.team.localeCompare(b.team))
  const discoverableTeams = [...new Set(teams)].filter(team => team.toLowerCase().includes(query.toLowerCase())).sort((a, b) => a.localeCompare(b))
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
    <p>{view === 'trajectory' ? 'Compare ten-year direction and three-year momentum using the shared historical program research. Missing verified coverage is not inferred.' : view === 'hype' ? 'Compare preseason AP and Coaches expectations with final Top 25 results. Unranked is never treated as a fabricated rank 26. Historical tendency requires all ten seasons.' : 'Opponent-adjusted historical strength, not current-season power rankings. A rank is only shown when all seasons in the selected window have verified coverage.'}</p>
    {error && <p role="status">{error} No rankings are estimated from missing data.</p>}
    {data && <><p>Through the {data.latest_completed_season} completed season · Descriptive research only</p>
      {view === 'trajectory' ? null : view === 'hype' ? <label>Poll <select value={poll} onChange={e => setPoll(e.target.value as 'AP' | 'Coaches')}><option value="AP">AP Poll</option><option value="Coaches">Coaches Poll</option></select></label> : <label>Ranking window <select value={window} onChange={e => setWindow(e.target.value as '10' | '5' | '3')}><option value="10">10 seasons</option><option value="5">5 seasons</option><option value="3">3 seasons</option></select></label>}
      <input aria-label="Search historical programs" placeholder="Search programs…" value={query} onChange={e => setQuery(e.target.value)} />
      {view === 'trajectory' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>10-year trajectory</th><th>3-year momentum</th><th>10-year rank</th><th>5-year rank</th><th>3-year rank</th></tr></thead><tbody>{programs.map(p => <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{p.program_rankings?.['10']?.rank ?? '—'}</td><td>{p.program_rankings?.['5']?.rank ?? '—'}</td><td>{p.program_rankings?.['3']?.rank ?? '—'}</td></tr>)}</tbody></table></div> : view === 'hype' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>Historical tendency</th><th>Seasons</th><th>Preseason Top 25</th><th>Dropped out</th><th>Entered Top 25</th></tr></thead><tbody>{programs.map(p => { const h = p.hype[poll]; return <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{h?.historical_tendency.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{h?.seasons_observed ?? '—'} / 10</td><td>{h?.preseason_top25 ?? '—'}</td><td>{h?.dropped_out ?? '—'}</td><td>{h?.entered_top25 ?? '—'}</td></tr> })}</tbody></table></div> : <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Program</th><th>Strength</th><th>Verified seasons</th><th>Source details</th><th>10-year trajectory</th><th>3-year momentum</th><th>AP hype</th><th>Coaches hype</th></tr></thead><tbody>{programs.map(p => {
        const score = p.program_rankings?.[window]
        return <tr key={p.team}><td>{score?.rank ?? '—'}</td><td className="team"><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{score?.strength == null ? 'Insufficient data' : score.strength.toFixed(2)}</td><td>{score ? `${score.seasons_available}/${score.seasons_required}` : 'Unavailable'}</td><td>{score?.sources?.length ? <details><summary>{score.sources.length} sources</summary><ul>{score.sources.map(entry => <li key={entry.season}>{entry.season}: {entry.source}</li>)}</ul></details> : 'Not published'}</td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || '—'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || '—'}</td><td>{p.hype.AP?.historical_tendency.replaceAll('_', ' ') || '—'}</td><td>{p.hype.Coaches?.historical_tendency.replaceAll('_', ' ') || '—'}</td></tr>
      })}</tbody></table></div>}
      {view === 'rankings' && <p>Only complete, independently reviewed historical windows receive a rank. Coverage shows available seasons versus required seasons; a missing rank is not a zero score.</p>}
      {!programs.length && <p>No programs match this search.</p>}
    </>}
  </section>
}
