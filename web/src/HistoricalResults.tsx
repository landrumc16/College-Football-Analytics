import { useEffect, useState } from 'react'
type Window = { wins: number; losses: number; win_pct: number; seasons: number[] }
type Row = { team: string; windows: Record<string, Window> }
type Payload = { schema_version: number; status: string; source_review_attested: boolean; national_grades_available: boolean; latest_completed_season: number; excluded_seasons: number[]; programs: Row[] }
function valid(p: Payload): boolean {
  return p?.schema_version === 1 && p.status === 'research_preview_not_independently_source_attested' &&
    p.source_review_attested === false && p.national_grades_available === false &&
    p.latest_completed_season === 2025 && JSON.stringify(p.excluded_seasons) === '[2020]' &&
    Array.isArray(p.programs) && p.programs.length >= 120 &&
    new Set(p.programs.map(r => r.team)).size === p.programs.length &&
    p.programs.every(r => typeof r.team === 'string' && r.team.length > 0 &&
      ['3','5','10'].every(key => { const w=r.windows?.[key]; return !w || (
        Number.isInteger(w.wins) && w.wins >= 0 && Number.isInteger(w.losses) && w.losses >= 0 &&
        w.wins+w.losses > 0 && Math.abs(w.win_pct-w.wins/(w.wins+w.losses)) <= 0.000051 &&
        Array.isArray(w.seasons) && !w.seasons.includes(2020)) }))
}
export default function HistoricalResults({ onTeam }: { onTeam: (team: string) => void }) {
  const [data, setData] = useState<Payload | null>(null)
  const [message, setMessage] = useState('')
  const [span, setSpan] = useState('10')
  const [query, setQuery] = useState('')
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL+'v5-historical-results-preview.json', {cache:'no-store'})
      .then(r => { if (!r.ok) throw new Error('National historical results are not yet published'); return r.json() })
      .then((value: Payload) => { if (!valid(value)) throw new Error('Historical research failed integrity checks'); if(active) setData(value) })
      .catch(e => { if(active) setMessage(String(e.message||e)) })
    return () => { active=false }
  }, [])
  const rows=(data?.programs||[]).filter(r=>r.team.toLowerCase().includes(query.toLowerCase())).sort((a,b)=>
    (b.windows[span]?.win_pct ?? -1)-(a.windows[span]?.win_pct ?? -1)||a.team.localeCompare(b.team))
  return <section className="accuracy-summary" aria-label="Historical FBS results">
    <h3>Historical FBS results · 2016–2025</h3>
    <p>Actual completed FBS-versus-FBS wins and losses. Compare 3-, 5-, and 10-year windows, excluding the disrupted 2020 season. These are <strong>unadjusted win percentages</strong>, not strength rankings, national grades, or forecasts. Independent source review remains outstanding.</p>
    {data ? <><p>{data.programs.length} programs represented · {data.programs.filter(r=>r.windows[span]).length} with complete selected-window coverage.</p>
      <label>Window <select aria-label="Historical results window" value={span} onChange={e=>setSpan(e.target.value)}><option value="3">3 years</option><option value="5">5 years</option><option value="10">10 years (2020 excluded)</option></select></label>
      <label>Search <input aria-label="Search historical results" value={query} onChange={e=>setQuery(e.target.value)} /></label>
      <div className="table-wrap"><table><thead><tr><th>Program</th><th>FBS wins</th><th>FBS losses</th><th>Win %</th><th>Seasons</th></tr></thead><tbody>{rows.map(r=>{const w=r.windows[span];return <tr key={r.team}><td><button type="button" onClick={()=>onTeam(r.team)}>{r.team}</button></td><td>{w?.wins ?? '—'}</td><td>{w?.losses ?? '—'}</td><td>{w ? (100*w.win_pct).toFixed(1)+'%' : 'N/A'}</td><td>{w?.seasons.join(', ') ?? 'Insufficient coverage'}</td></tr>})}</tbody></table></div>
    </> : <p role="status">{message || 'Loading national historical results…'}</p>}
    <small>Research preview only. Poll identity, historical Hype Index, source attestations, and national peer-relative grades require separate verification.</small>
  </section>
}
