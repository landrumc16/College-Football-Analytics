import { useEffect, useState } from 'react'
type Stats = { games: number; accuracy: number; brier: number; logloss: number; confidence_segments: Record<string, { games: number; accuracy: number | null; brier: number | null }> }
type Evidence = { status: string; evaluation_scope: string; outcome_as_of: string; eligible_completed_games: number; forecast_coverage: number; forecast_publication: { workflow_url: string }; models: Record<string, Stats> }
export default function ForecastEvidence() {
  const [data, setData] = useState<Evidence | null>(null)
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v5-forecast-evaluation.json', { cache: 'no-store' })
      .then(r => { if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw new Error('Unavailable'); return r.json() })
      .then((value: Evidence) => { if (active && value.status === 'independently_verified_published_pregame_subset' && value.models?.workbook_2026_baseline?.games > 0) setData(value) }).catch(() => {})
    return () => { active = false }
  }, [])
  const score = data?.models.workbook_2026_baseline
  const baseline = data?.models.neutral_50_50
  return data && score ? <section aria-label="Independent pregame forecast verification" className="accuracy-summary">
    <h3>Independently verified forecast archive</h3>
    <p>{data.evaluation_scope}: {score.games} predictions published before kickoff and matched to independent NCAA final scores. Outcomes as of {data.outcome_as_of}.</p>
    <p>Correct winners {(score.accuracy * 100).toFixed(1)}% · Brier {score.brier.toFixed(4)} · log loss {score.logloss.toFixed(4)}. Coverage: {score.games} of {data.eligible_completed_games} eligible completed games ({(data.forecast_coverage * 100).toFixed(1)}%). This is one week, not full-season or future accuracy.</p>
    {baseline && <p>Same-game neutral 50/50 reference: Brier {baseline.brier.toFixed(4)} · log loss {baseline.logloss.toFixed(4)}. Lower is better; this reference is not a competing forecast model.</p>}
    <div className="table-wrap"><table><thead><tr><th>Predicted winner confidence</th><th>Games</th><th>Winner accuracy</th><th>Brier</th></tr></thead><tbody>{Object.entries(score.confidence_segments).map(([segment, s]) => <tr key={segment}><td>{segment === 'low' ? '50–60%' : segment === 'medium' ? '60–75%' : '75–100%'}</td><td>{s.games}</td><td>{s.accuracy == null ? 'N/A' : `${(100 * s.accuracy).toFixed(1)}%`}</td><td>{s.brier?.toFixed(4) ?? 'N/A'}</td></tr>)}</tbody></table></div>
    <p><a href={data.forecast_publication.workflow_url} target="_blank" rel="noreferrer">Original pre-kickoff publication</a>. Retrospective studies and incomplete legacy records are excluded.</p>
  </section> : null
}
