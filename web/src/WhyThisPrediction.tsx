import { useEffect, useState } from 'react'
import { explain, type ExplanationData } from './predictionExplanations'
import './prediction-explanations.css'

// One shared request for every prediction card on the page.
let request: Promise<ExplanationData | null> | null = null
function loadExplanations() {
  request ??= fetch(import.meta.env.BASE_URL + 'prediction-explanations.json', { cache: 'no-store' })
    .then(r => (r.ok && r.headers.get('content-type')?.includes('json') ? r.json() : null))
    .then((d: ExplanationData | null) => (d?.games && d?.teams ? d : null))
    .catch(() => null)
  return request
}

const pts = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(1)}`

/** Body of the prediction card's "Why this prediction?" expander. Falls back to the published summary. */
export default function WhyThisPrediction({ gameId, homeMargin, fallback }: { gameId: number; homeMargin: number; fallback: string }) {
  const [data, setData] = useState<ExplanationData | null | undefined>(undefined)
  useEffect(() => { let on = true; loadExplanations().then(d => { if (on) setData(d) }); return () => { on = false } }, [])
  if (data === undefined) return <p role="status">{fallback}</p>
  // Only explain the forecast actually shown on the card (the two files refresh together at deploy).
  const game = data?.games.find(g => g.game_id === gameId && Math.abs(g.official.home_margin - homeMargin) < 0.01)
  const e = game && data ? explain(game, data) : null
  const stale = !game && data?.games.some(g => g.game_id === gameId)
  if (!e) return <><p>{fallback}</p><p className="wp-muted">{stale ? 'The factor-by-factor explanation is being refreshed with the latest results.' : 'A factor-by-factor explanation is available for games between two FBS teams.'}</p></>
  return <div className="why-prediction">
    <p className="wp-bottom">{e.bottomLine}</p>
    <p className="wp-muted">{e.headline}</p>
    <dl className="wp-factors">{e.factors.map(f => <div key={f.key}><dt>{f.title}</dt><dd>{f.text}</dd></div>)}</dl>
    {e.notes.map(n => <p key={n} className="wp-note">{n}</p>)}
    <details className="wp-numbers"><summary>See How Each Forecast Adds Up</summary>
      <div className="table-wrap"><table>
        <caption>Points Toward {e.favourite} (Negative Favors {e.underdog})</caption>
        <thead><tr><th scope="col">Forecast</th><th scope="col">This Season</th><th scope="col">Last Season</th><th scope="col">Home Field</th><th scope="col">Total</th></tr></thead>
        <tbody>{e.models.map(r => <tr key={r.model}><th scope="row">{r.model}</th><td>{pts(r.season)}</td><td>{pts(r.prior)}</td><td>{pts(r.home)}</td><td><b>{pts(r.total)}</b></td></tr>)}</tbody>
      </table></div>
      <p>{e.modelDifference}</p>
    </details>
    <p className="wp-muted"><strong>Not included in any model:</strong> {e.unavailable.join('; ')}.</p>
  </div>
}
