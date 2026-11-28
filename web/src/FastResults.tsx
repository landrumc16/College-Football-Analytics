import { useEffect, useState } from 'react'
import { parseFastResults, type FastResults as Feed, type FastScheduleGame } from './fastResults'

export default function FastResults({ schedule }: { schedule: FastScheduleGame[] }) {
  const [feed, setFeed] = useState<Feed | null>(null)
  // A missing optional feed is normal until an authorized rapid source is configured.
  const identity = JSON.stringify(schedule)
  useEffect(() => {
    let active = true
    const load = () => fetch(import.meta.env.BASE_URL + 'fast-results.json', { cache: 'no-store' })
      .then(r => { if (!r.ok) throw Error(); return r.json() })
      .then(value => { if (active) setFeed(parseFastResults(value, JSON.parse(identity))) })
      .catch(() => { if (active) setFeed(null) })
    void load()
    const timer = window.setInterval(load, 60_000)
    return () => { active = false; window.clearInterval(timer) }
  }, [identity])
  if (!feed?.events.length) return null
  return <section className="notice" aria-label="Rapid game results">
    <h2>Game Results</h2>
    <p>Provisional scores await CFBD verification.</p>
    <p><small>Updated: {feed.generated_at}</small></p>
    {feed.events.map(game => <div key={game.game_id}>
      <h3>{game.away} {game.away_score} · {game.home} {game.home_score}</h3>
      <p><strong>{game.status === 'provisional' ? 'Provisional Final' : game.status === 'disputed' ? (game.model_ingestion_allowed ? 'Verified Final — Update Disputed' : 'Disputed — Pending') : game.status === 'corrected' ? 'Corrected — CFBD Verified' : 'Verified Final'}</strong>{' '}· <a href={game.source}>Source</a></p>
      <p>{game.statistics_pending ? 'Statistics pending. ' : 'Advanced stats separate. '}{game.basic_stats && !game.statistics_verified && 'Provisional statistics.'}</p>
      {game.basic_stats && (['away', 'home'] as const).map(side => <p key={side}>{game[side]} · {Object.entries(game.basic_stats?.[side] as Record<string, unknown> ?? {}).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${typeof value === 'number' && Number.isFinite(value) ? value : 'Pending'}`).join(' · ')}</p>)}
      <p>{[game.away, game.home].filter(team => feed.records[team]).map(team => { const r = feed.records[team]; return `${team}: ${r.wins}–${r.losses}${r.provisional_games ? ' (provisional)' : ''}` }).join(' · ')}</p>
    </div>)}
  </section>
}
