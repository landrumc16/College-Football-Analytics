import { useEffect, useState } from 'react'

type Category = { score: number | null; grade: string | null }
type Hype = { seasons: number; preseason_top25: number; retained_top25: number; dropped_out: number; entered_top25: number; ranked_to_ranked_movement: number }
type Trajectory = { windows: Record<string, number>; annual_slopes: Record<string, number>; direction: string; value: number }
type Program = { team: string; categories: Record<'hype' | 'trajectory' | 'strength', Category>; overall_score: number | null; overall_grade: string | null; hype?: Record<string, Hype>; trajectory?: Trajectory | null }
export type Report = { schema_version: number; as_of: string; peer_universe: string; eligible_fbs_count: number; source_review: { polls: boolean; historical_results: boolean; incumbent_strength: boolean }; sources: string[]; coverage: Record<string, { verified: number; eligible: number; national_grades_available: boolean }>; programs: Program[] }

export function validReportCards(report: Report): boolean {
  return report?.schema_version === 1 && report.peer_universe === 'eligible_FBS' &&
    Number.isInteger(report.eligible_fbs_count) && report.eligible_fbs_count >= 120 &&
    typeof report.as_of === 'string' && !!report.as_of &&
    Array.isArray(report.sources) && report.sources.length > 0 && report.sources.every(s => s.startsWith('https://')) &&
    Array.isArray(report.programs) && report.programs.length === report.eligible_fbs_count && new Set(report.programs.map(p => p.team)).size === report.eligible_fbs_count &&
    ['hype', 'trajectory', 'strength'].every(k => {
      const c = report.coverage?.[k]
      const reviewed = report.source_review?.[k === 'hype' ? 'polls' : k === 'trajectory' ? 'historical_results' : 'incumbent_strength']
      return c && typeof c.national_grades_available === 'boolean' && Number.isInteger(c.verified) && c.eligible === report.eligible_fbs_count && c.verified >= 0 && c.verified <= c.eligible && (!c.national_grades_available || reviewed === true && c.verified / c.eligible >= .8)
    }) && report.programs.every(p => typeof p.team === 'string' && !!p.team &&
      ['hype', 'trajectory', 'strength'].every(k => {
        const c = p.categories?.[k as 'hype' | 'trajectory' | 'strength']
        return c && (c.score === null && c.grade === null || report.coverage[k].national_grades_available &&
          typeof c.grade === 'string' && typeof c.score === 'number' && Number.isFinite(c.score) && c.score >= 0 && c.score <= 100)
      }) && (p.overall_score === null && p.overall_grade === null ||
        ['hype', 'trajectory', 'strength'].every(k => p.categories[k as keyof typeof p.categories].score !== null) &&
        typeof p.overall_score === 'number' && Number.isFinite(p.overall_score) &&
        Math.abs(p.overall_score - (p.categories.hype.score! + p.categories.trajectory.score! + p.categories.strength.score!) / 3) < 1e-9 && typeof p.overall_grade === 'string'))
}
const display = (category?: Category) => category?.grade != null && category.score != null
  ? `${category.grade} (${category.score.toFixed(1)})` : 'N/A'
const percentage = (v?: number) => v == null ? 'N/A' : `${(100 * v).toFixed(1)}%`
export function useReportCards() {
  const [report, setReport] = useState<Report | null>(null)
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v5-program-report-cards.json', { cache: 'no-store' })
      .then(r => { if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw new Error('Not published'); return r.json() })
      .then((data: Report) => { if (active && validReportCards(data)) setReport(data) })
      .catch(() => { if (active) setReport(null) })
    return () => { active = false }
  }, [])
  return report
}
function Card({ team, report }: { team: string; report: Report | null }) {
  const record = report?.programs.find(p => p.team === team)
  const publishedCategories = (['hype', 'trajectory', 'strength'] as const).filter(k => report?.coverage[k]?.national_grades_available)
  return <section className="accuracy-summary" aria-label={`CFA Program Report Card for ${team}`}>
    <h3>{team} · CFA Program Report Card</h3>
    <p>Three independent peer-relative grades, equally weighted. Overall: <strong>{record?.overall_grade != null && record.overall_score != null ? `${record.overall_grade} (${record.overall_score.toFixed(1)}/100)` : 'N/A — awaiting all three reviewed categories'}</strong></p>
    <div className="team-profile-grid">
      {(['hype', 'trajectory', 'strength'] as const).map(k => <div className="team-profile-tile" key={k}>
        <small>{k === 'hype' ? 'Hype Index' : k === 'trajectory' ? 'Program Trajectory' : 'Program Strength'}</small>
        <strong>{report?.coverage[k]?.national_grades_available ? display(record?.categories?.[k]) : 'N/A'}</strong>
      </div>)}
    </div>
    {record?.trajectory && <p>2016–2025 FBS win rates: 3 years {percentage(record.trajectory.windows['3'])} · 5 years {percentage(record.trajectory.windows['5'])} · 10 years {percentage(record.trajectory.windows['10'])}. Direction: <strong>{record.trajectory.direction}</strong> ({(100 * record.trajectory.value).toFixed(2)} percentage points/year). Disrupted 2020 excluded.</p>}
    {record?.hype && Object.entries(record.hype).map(([poll, h]) => <p key={poll}>{poll}, {h.seasons} seasons: preseason Top 25 {h.preseason_top25} · retained {h.retained_top25} · dropped out {h.dropped_out} · unranked to Top 25 {h.entered_top25} · ranked-to-ranked net movement {h.ranked_to_ranked_movement > 0 ? '+' : ''}{h.ranked_to_ranked_movement}.</p>)}
    <p>{report ? `Current strength as of ${report.as_of}; eligible FBS peer universe: ${report.eligible_fbs_count} programs. Verified Hype ${report.coverage.hype.verified}, Trajectory ${report.coverage.trajectory.verified}, Strength ${report.coverage.strength.verified}.` : 'Reviewed national report cards have not been published.'} {publishedCategories.length > 0 && publishedCategories.length < 3 ? 'Available categories are shown independently.' : ''} Missing historical coverage is N/A; category percentiles use eligible peers with sufficient evidence.</p>
    <details><summary>Report Card methods and sources</summary><p>Hype measures expectation management using AP and Coaches preseason-to-final movement. Unranked uses a capped boundary value of 26 for the index only, never an asserted poll rank; unranked-to-unranked is neutral. Trajectory measures direction using the mean annual win-rate slope in 3/5/10-year windows; within ±1 percentage point/year is stable. Strength uses the incumbent current-season rating. Each category uses midrank percentiles; ties share a score. Overall is the unrounded arithmetic mean of all three scores. These grades are descriptive, not win probabilities.</p>{report?.sources.map(s => <p key={s}><a href={s} target="_blank" rel="noreferrer">{s.includes('ncaa_mfb_teams') ? 'Independent NCAA FBS roster' : 'Retained inputs, comparisons and exceptions'}</a></p>)}</details>
  </section>
}
export default function ProgramReportCard({ team }: { team: string }) {
  return <Card team={team} report={useReportCards()} />
}
export function ReportCardExplorer({ report, onTeam, conferenceTeams, view }: { report: Report; onTeam: (team: string) => void; conferenceTeams: Record<string, string[]>; view: string }) {
  const [query, setQuery] = useState('')
  const [conference, setConference] = useState('all')
  const [poll, setPoll] = useState('AP')
  const [selected, setSelected] = useState('')
  const [all, setAll] = useState(false)
  const category = view === 'hype' ? 'hype' : 'trajectory'
  const rows = report.programs.filter(p => p.team.toLowerCase().includes(query.toLowerCase()) && (conference === 'all' || conferenceTeams[conference]?.includes(p.team))).sort((a, b) => (b.categories[category].score ?? -1) - (a.categories[category].score ?? -1) || a.team.localeCompare(b.team))
  return <section aria-label="Verified national historical intelligence">
    <p>Independently corroborated 2016–2025 evidence. National grades use {report.eligible_fbs_count} eligible FBS programs; incomplete historical windows remain N/A.</p>
    <label>Search <input aria-label="Search historical programs" value={query} onChange={e => setQuery(e.target.value)} /></label>
    <label>Conference <select aria-label="Filter historical programs by conference" value={conference} onChange={e => setConference(e.target.value)}><option value="all">All conferences</option>{Object.keys(conferenceTeams).sort().map(c => <option key={c}>{c}</option>)}</select></label>
    {view === 'hype' && <label>Poll <select aria-label="Historical expectations poll" value={poll} onChange={e => setPoll(e.target.value)}><option>AP</option><option>Coaches</option></select></label>}
    <label>Program <select aria-label="Choose historical program" value={selected} onChange={e => setSelected(e.target.value)}><option value="">Select a program</option>{report.programs.map(p => <option key={p.team}>{p.team}</option>)}</select></label>
    {selected && <Card team={selected} report={report} />}
    <div className="table-wrap"><table><thead><tr><th>Program</th><th>{view === 'hype' ? 'Hype grade' : 'Trajectory grade'}</th>{view === 'hype' ? <><th>Preseason Top 25</th><th>Retained</th><th>Dropped out</th><th>New entrants</th></> : <><th>3-year win %</th><th>5-year win %</th><th>10-year win %</th><th>Direction</th></>}</tr></thead><tbody>{(all ? rows : rows.slice(0, 25)).map(p => <tr key={p.team}><td><button type="button" onClick={() => onTeam(p.team)}>{p.team}</button></td><td>{display(p.categories[category])}</td>{view === 'hype' ? <><td>{p.hype?.[poll]?.preseason_top25 ?? 'N/A'}</td><td>{p.hype?.[poll]?.retained_top25 ?? 'N/A'}</td><td>{p.hype?.[poll]?.dropped_out ?? 'N/A'}</td><td>{p.hype?.[poll]?.entered_top25 ?? 'N/A'}</td></> : <><td>{percentage(p.trajectory?.windows['3'])}</td><td>{percentage(p.trajectory?.windows['5'])}</td><td>{percentage(p.trajectory?.windows['10'])}</td><td>{p.trajectory?.direction ?? 'N/A'}</td></>}</tr>)}</tbody></table></div>
    {rows.length > 25 && <button type="button" onClick={() => setAll(!all)}>{all ? 'Show first 25 programs' : `Show all ${rows.length} programs`}</button>}
    {!rows.length && <p role="status">No programs match this search.</p>}
  </section>
}
