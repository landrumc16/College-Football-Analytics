import { useEffect, useState } from 'react'

type WindowScore = { rank: number | null; strength: number | null; seasons_available: number; seasons_required: number }
type Program = { team: string; program_rankings: Record<string, WindowScore> | null; trajectory: { long_term: { classification: string }; recent: { classification: string } } | null; hype: Record<string, { historical_tendency: string; dropped_out: number; entered_top25: number; seasons_observed: number; preseason_top25: number }> }
type Payload = { schema_version: number; status: string; latest_completed_season: number; programs: Program[] }

export default function ProgramIntelligence({ onTeam, view = 'rankings' }: { onTeam: (team: string) => void; view?: 'rankings' | 'hype' }) {
  const [data, setData] = useState<Payload | null>(null)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [poll, setPoll] = useState<'AP' | 'Coaches'>('AP')
  const [window, setWindow] = useState<'10' | '5' | '3'>('10')
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v4-program-intelligence.json', { cache: 'no-store' })
      .then(response => { if (!response.ok) throw new Error('Verified historical program data has not been published yet.'); return response.json() })
      .then((payload: Payload) => {
        if (active) {
          if (payload.schema_version !== 1 || payload.status !== 'descriptive_only' || !Array.isArray(payload.programs)) throw new Error('Unsupported historical research format.')
          setData(payload)
        }
      })
      .catch(e => { if (active) setError(String(e.message || e)) })
    return () => { active = false }
  }, [])
  const programs = (data?.programs || []).filter(p => p.team.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => view === 'hype' ? (b.hype[poll]?.dropped_out ?? -1) - (a.hype[poll]?.dropped_out ?? -1) || a.team.localeCompare(b.team) : (a.program_rankings?.[window]?.rank ?? Infinity) - (b.program_rankings?.[window]?.rank ?? Infinity) || a.team.localeCompare(b.team))
  return <section className="notice">
    <h2>{view === 'hype' ? 'Historical Hype Index' : 'Historical Program Rankings'}</h2>
    <p>{view === 'hype' ? 'Compare preseason AP and Coaches expectations with final Top 25 results. Unranked is never treated as a fabricated rank 26. Historical tendency requires all ten seasons.' : 'Opponent-adjusted historical strength, not current-season power rankings. A rank is only shown when all seasons in the selected window have verified coverage.'}</p>
    {error && <p role="status">{error} No rankings are estimated from missing data.</p>}
    {data && <><p>Through the {data.latest_completed_season} completed season · Descriptive research only</p>
      {view === 'hype' ? <label>Poll <select value={poll} onChange={e => setPoll(e.target.value as 'AP' | 'Coaches')}><option value="AP">AP Poll</option><option value="Coaches">Coaches Poll</option></select></label> : <label>Ranking window <select value={window} onChange={e => setWindow(e.target.value as '10' | '5' | '3')}><option value="10">10 seasons</option><option value="5">5 seasons</option><option value="3">3 seasons</option></select></label>}
      <input aria-label="Search historical programs" placeholder="Search programs…" value={query} onChange={e => setQuery(e.target.value)} />
      {view === 'hype' ? <div className="table-wrap"><table><thead><tr><th>Program</th><th>Historical tendency</th><th>Seasons</th><th>Preseason Top 25</th><th>Dropped out</th><th>Entered Top 25</th></tr></thead><tbody>{programs.map(p => { const h = p.hype[poll]; return <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{h?.historical_tendency.replaceAll('_', ' ') || 'Insufficient data'}</td><td>{h?.seasons_observed ?? '—'} / 10</td><td>{h?.preseason_top25 ?? '—'}</td><td>{h?.dropped_out ?? '—'}</td><td>{h?.entered_top25 ?? '—'}</td></tr> })}</tbody></table></div> : <div className="table-wrap"><table><thead><tr><th>Rank</th><th>Program</th><th>Strength</th><th>10-year trajectory</th><th>3-year momentum</th><th>AP hype</th><th>Coaches hype</th></tr></thead><tbody>{programs.map(p => {
        const score = p.program_rankings?.[window]
        return <tr key={p.team}><td>{score?.rank ?? '—'}</td><td className="team"><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{score?.strength == null ? 'Insufficient data' : score.strength.toFixed(2)}</td><td>{p.trajectory?.long_term.classification.replaceAll('_', ' ') || '—'}</td><td>{p.trajectory?.recent.classification.replaceAll('_', ' ') || '—'}</td><td>{p.hype.AP?.historical_tendency.replaceAll('_', ' ') || '—'}</td><td>{p.hype.Coaches?.historical_tendency.replaceAll('_', ' ') || '—'}</td></tr>
      })}</tbody></table></div>}
      {!programs.length && <p>No programs match this search.</p>}
    </>}
  </section>
}
