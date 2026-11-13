import { useEffect, useState } from 'react'

type HistoricalRow = { team: string; completed_fbs_games_by_season: number[]; total_completed_fbs_games: number }
type HistoricalCoverage = { schema_version: number; status: string; metric: string; seasons: number[]; programs: HistoricalRow[] }
function valid(data: HistoricalCoverage): boolean {
  return data?.schema_version === 1 && data.status === 'research_only_not_publishable' &&
    data.metric === 'Completed FBS-versus-FBS games (not wins, strength, rankings or grades)' &&
    Array.isArray(data.seasons) && data.seasons.length === 10 &&
    data.seasons.every((year, index) => year === 2016 + index) &&
    Array.isArray(data.programs) && data.programs.length > 0 &&
    new Set(data.programs.map(p => p.team)).size === data.programs.length &&
    data.programs.every(p => !!p.team && p.completed_fbs_games_by_season?.length === 10 &&
      p.completed_fbs_games_by_season.every(n => Number.isInteger(n) && n >= 0) &&
      p.total_completed_fbs_games === p.completed_fbs_games_by_season.reduce((a, b) => a + b, 0))
}
export default function HistoricalGameCoverage({ onTeam }: { onTeam: (team: string) => void }) {
  const [data, setData] = useState<HistoricalCoverage | null>(null)
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v5-historical-games-research.json', { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error('Historical research unavailable'); return r.json() })
      .then((value: HistoricalCoverage) => {
        if (!valid(value)) throw new Error('Historical research integrity check failed')
        if (active) setData(value)
      })
      .catch(e => { if (active) setError(String(e.message || e)) })
    return () => { active = false }
  }, [])
  return <section className="accuracy-summary" aria-label="Historical FBS game coverage research">
    <h3>Historical FBS game coverage · 2016–2025</h3>
    <p>Archived completed FBS-versus-FBS game counts for the documented research cohort. These are <strong>games played, not wins</strong>. This descriptive research has not received independent source-review attestation; it is not a Hype Index, strength ranking, trajectory grade, or prediction evaluation.</p>
    {data ? <><p>{data.programs.length} documented programs · 2020 shown separately because schedules were disrupted.</p>
      <div className="table-wrap"><table><thead><tr><th>Program</th><th>2016–2019 games</th><th>2020 games</th><th>2021–2025 games</th><th>All 10 seasons</th></tr></thead><tbody>
      {data.programs.map(p => <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{p.completed_fbs_games_by_season.slice(0, 4).reduce((a,b)=>a+b,0)}</td><td>{p.completed_fbs_games_by_season[4]}</td><td>{p.completed_fbs_games_by_season.slice(5).reduce((a,b)=>a+b,0)}</td><td>{p.total_completed_fbs_games}</td></tr>)}
      </tbody></table></div></> : <p role="status">{error || 'Loading historical game coverage…'}</p>}
    <p><small>Source: archived V4 historical game artifacts. Independent source verification and national peer coverage are required before publishing grades.</small></p>
  </section>
}
