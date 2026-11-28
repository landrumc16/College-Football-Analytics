import { useEffect, useState } from 'react'
import { parseFastResults, type FastResults as Feed } from './fastResults'

export default function FastResults({ teams }: { teams: string[] }) {
  const [feed, setFeed] = useState<Feed | null>(null)
  // A missing optional feed is normal until an authorized rapid source is configured.
  const identity = teams.join('\n')
  useEffect(() => {
    const controller = new AbortController()
    let stopped = false
    const load = () => fetch(import.meta.env.BASE_URL + 'fast-results.json', { cache: 'no-store', signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error('Optional feed unavailable'); return r.json() })
      .then(value => { if (!stopped) setFeed(parseFastResults(value, identity.split('\n'))) })
      .catch(() => { if (!stopped) setFeed(null) })
    void load()
    const timer = window.setInterval(load, 60_000)
    return () => { stopped = true; controller.abort(); window.clearInterval(timer) }
  }, [identity])
  if (!feed?.events.length) return null
  return <section className="notice" aria-label="Rapid game results">
    <h2>Latest Game Results</h2>
    <p>Rapid results are separate from the season report. Provisional scores await CFBD verification; season ratings and predictions retain their own update time.</p>
    <p><small>Observed feed update: {new Date(feed.generated_at).toLocaleString()}</small></p>
    {feed.events.map(game => <article key={game.game_id}>
      <h3>{game.away} {game.away_score} · {game.home} {game.home_score}</h3>
      <p><strong>{game.status === 'provisional' ? 'Provisional Final — Awaiting Verification' : game.status === 'disputed' ? (game.model_ingestion_allowed ? 'Previously Verified Result Retained — New Report Disputed' : 'Disputed Result — Verification Pending') : game.status === 'corrected' ? 'Corrected Final — CFBD Verified' : 'Final — Verified'}</strong>{' '}· <a href={game.source} target="_blank" rel="noopener noreferrer">Source</a></p>
      <p>{game.statistics_pending ? 'Detailed statistics pending.' : 'Detailed statistics received.'}</p>
      {game.basic_stats && <div className="table-wrap"><table><caption>Basic Game Statistics{game.status === 'provisional' ? ' — Provisional' : ''}</caption><thead><tr><th>Team</th><th>Total Yards</th><th>Passing</th><th>Rushing</th><th>Turnovers</th></tr></thead><tbody>{(['away', 'home'] as const).map(side => {
        const stats = game.basic_stats?.[side] as Record<string, unknown> | undefined
        const cell = (key: string) => typeof stats?.[key] === 'number' && Number.isFinite(stats[key]) ? String(stats[key]) : 'Pending'
        return <tr key={side}><td>{game[side]}</td><td>{cell('total_yards')}</td><td>{cell('passing_yards')}</td><td>{cell('rushing_yards')}</td><td>{cell('turnovers')}</td></tr>
      })}</tbody></table></div>}
      <p>{[game.away, game.home].filter(team => feed.records[team]).map(team => { const r = feed.records[team]; return `${team}: ${r.wins}–${r.losses}${r.provisional_games ? ' (includes provisional results)' : ''}` }).join(' · ')}</p>
    </article>)}
  </section>
}
