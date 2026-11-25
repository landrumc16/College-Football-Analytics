import { useEffect, useState } from 'react'

type Game = { game_id: number; home: string; away: string; neutral_site: boolean; start_date: string | null; label: string
  completed: boolean; home_score: number | null; away_score: number | null
  prediction?: { home_margin: number; home_win_probability: number; predicted_winner: string } }
type Postseason = { season: number; retrieved_at: string; games: Game[] }

const pct = (p: number) => `${Math.round(100 * p)}%`
const when = (iso: string | null) => iso ? new Date(iso).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) : 'Date TBA'

/** Conference championships filed as postseason, bowls and CFP games. Hidden until CFBD lists postseason games. */
export default function PostseasonGames() {
  const [data, setData] = useState<Postseason | null>(null)
  useEffect(() => {
    let on = true
    fetch(import.meta.env.BASE_URL + 'postseason-2026.json', { cache: 'no-store' })
      .then(r => (r.ok && r.headers.get('content-type')?.includes('json') ? r.json() : null))
      .then((d: Postseason | null) => { if (on && d?.games?.length) setData(d) })
      .catch(() => {})
    return () => { on = false }
  }, [])
  if (!data) return null
  const upcoming = data.games.filter(g => !g.completed), finals = data.games.filter(g => g.completed)
  return <section className="predictions-intro postseason" aria-labelledby="postseason-title">
    <h2 id="postseason-title">Bowls and College Football Playoff</h2>
    <p>Results update as games become final. Picks use the same model ratings as the regular season; postseason results are shown but do not change the ratings. Updated {new Date(data.retrieved_at).toLocaleString()}.</p>
    <div className="prediction-cards">
      {upcoming.map(g => { const p = g.prediction; const prob = p ? (p.predicted_winner === g.home ? p.home_win_probability : 1 - p.home_win_probability) : null
        return <article key={g.game_id} className="prediction-card">
          <div className="prediction-meta">{(g.label || 'Postseason').toUpperCase()} · {when(g.start_date)}</div>
          <div className="prediction-matchup"><span>{g.away}</span><span className="prediction-at">{g.neutral_site ? 'vs' : '@'}</span><span>{g.home}</span></div>
          {p && prob != null ? <div className="prediction-metrics"><div><small>Model Pick</small><strong>{p.predicted_winner}</strong></div><div><small>Win Probability</small><strong>{pct(prob)}</strong></div></div>
            : <p className="muted">No model pick: one team is outside the rated FBS field.</p>}
        </article> })}
      {finals.map(g => <article key={g.game_id} className="prediction-card">
        <div className="prediction-meta">{(g.label || 'Postseason').toUpperCase()} · FINAL</div>
        <div className="prediction-matchup"><span>{g.away} {g.away_score}</span><span className="prediction-at">{g.neutral_site ? 'vs' : '@'}</span><span>{g.home} {g.home_score}</span></div>
      </article>)}
    </div>
  </section>
}
