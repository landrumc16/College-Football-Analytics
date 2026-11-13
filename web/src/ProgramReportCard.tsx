import { useEffect, useState } from 'react'

type Category = { score: number | null; grade: string | null }
type Program = { team: string; categories: Record<'hype' | 'trajectory' | 'strength', Category>; overall_score: number | null; overall_grade: string | null }
type Report = { schema_version: number; as_of: string; peer_universe: string; eligible_fbs_count: number; coverage: Record<string, { national_grades_available: boolean }>; programs: Program[] }

function valid(report: Report): boolean {
  return report?.schema_version === 1 && report.peer_universe === 'eligible_FBS' &&
    Number.isInteger(report.eligible_fbs_count) && report.eligible_fbs_count >= 120 &&
    typeof report.as_of === 'string' && !!report.as_of &&
    Array.isArray(report.programs) && report.programs.length === report.eligible_fbs_count && new Set(report.programs.map(p => p.team)).size === report.eligible_fbs_count &&
    ['hype', 'trajectory', 'strength'].every(k => typeof report.coverage?.[k]?.national_grades_available === 'boolean') &&
    report.programs.every(p => typeof p.team === 'string' && !!p.team &&
      ['hype', 'trajectory', 'strength'].every(k => {
        const c = p.categories?.[k as 'hype' | 'trajectory' | 'strength']
        return c && (c.score === null && c.grade === null ||
          typeof c.grade === 'string' && typeof c.score === 'number' && Number.isFinite(c.score) && c.score >= 0 && c.score <= 100)
      }) &&
      (p.overall_score === null && p.overall_grade === null ||
        typeof p.overall_score === 'number' && Number.isFinite(p.overall_score) && p.overall_score >= 0 && p.overall_score <= 100 && typeof p.overall_grade === 'string'))
}
const display = (category?: Category) => category?.grade != null && category.score != null && Number.isFinite(category.score) && category.score >= 0 && category.score <= 100
  ? `${category.grade} (${category.score.toFixed(1)})` : 'N/A'

export default function ProgramReportCard({ team }: { team: string }) {
  const [report, setReport] = useState<Report | null>(null)
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v5-program-report-cards.json', { cache: 'no-store' })
      .then(r => { if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw new Error('Not published'); return r.json() })
      .then((data: Report) => { if (active && valid(data)) setReport(data) })
      .catch(() => { if (active) setReport(null) })
    return () => { active = false }
  }, [])
  const record = report?.programs.find(p => p.team === team)
  const available = !!record && ['hype', 'trajectory', 'strength'].every(k => report?.coverage[k].national_grades_available)
  const publishedCategories = (['hype', 'trajectory', 'strength'] as const).filter(k => report?.coverage[k]?.national_grades_available)
  const partial = !!report && publishedCategories.length > 0 && publishedCategories.length < 3
  return <section className="accuracy-summary" aria-label={`CFA Program Report Card for ${team}`}>
    <h3>CFA Program Report Card</h3>
    <p>Three independent peer-relative grades, equally weighted. Overall: <strong>{available && record.overall_grade != null && record.overall_score != null ? `${record.overall_grade} (${record.overall_score.toFixed(1)}/100)` : 'N/A — awaiting all three reviewed categories'}</strong></p>
    <div className="team-profile-grid">
      {(['hype', 'trajectory', 'strength'] as const).map(k => <div className="team-profile-tile" key={k}>
        <small>{k === 'hype' ? 'Hype Index' : k === 'trajectory' ? 'Program Trajectory' : 'Program Strength'}</small>
        <strong>{report?.coverage[k]?.national_grades_available ? display(record?.categories?.[k]) : 'N/A'}</strong>
      </div>)}
    </div>
    <p>{report ? `As of ${report.as_of}; eligible FBS peer universe: ${report.eligible_fbs_count} programs.` : 'Reviewed national report cards have not been published.'} {partial ? `${publishedCategories.length} of 3 categories have sufficient reviewed national coverage; available grades are shown independently.` : ''} These grades describe expectations, multi-season direction, and current quality—not win probabilities.</p>
  </section>
}
