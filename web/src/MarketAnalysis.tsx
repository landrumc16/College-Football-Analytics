import { titleCase } from './titleCase'
import { useEffect, useState } from 'react'
import MarketCalculator, { type ModelSource } from './MarketCalculator'

export type MarketGame = { game_id: number; week: number; home: string; away: string; neutral_site?: boolean; home_margin: number; home_win_probability: number }
type Props = { games: MarketGame[]; selectedId: number | null; onSelect: (id: number) => void; onCustom: () => void; sourceFor: (game: MarketGame) => ModelSource }

// The Market Analysis page: pick a game, enter a market number, read the comparison. History is secondary and lazy.
export default function MarketAnalysis({ games, selectedId, onSelect, onCustom, sourceFor }: Props) {
  const game = games.find(g => g.game_id === selectedId) ?? games[0]
  const [historyOpen, setHistoryOpen] = useState(false)
  const [teamQuery, setTeamQuery] = useState('')
  // Match either team's own name (case-insensitive, partial), never text spanning both names.
  const query = teamQuery.trim().toLowerCase()
  const matches = query ? games.filter(g => g.home.toLowerCase().includes(query) || g.away.toLowerCase().includes(query)) : []
  const choose = (id: number) => { onSelect(id); setTeamQuery('') }
  return <section className="market-analysis" aria-labelledby="market-analysis-title">
    <h2 id="market-analysis-title">Market Analysis</h2>
    <p className="page-deck">Pick a game, type the spread, probability or moneyline you see, and compare it with our model instantly. Educational only: not betting advice.</p>
    {!game ? <div className="notice"><p>No upcoming FBS-vs-FBS game has a published forecast right now.</p><button type="button" onClick={onCustom}>Compare Any Two Schools</button></div> : <>
      <div className="market-game-row">
        <label htmlFor="market-team-search">Find a Game by Team Name</label>
        <input id="market-team-search" type="search" autoComplete="off" value={teamQuery}
          placeholder="Search Texas Tech, Baylor, TCU…" aria-describedby="market-team-search-status" onChange={e => setTeamQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && matches.length) { e.preventDefault(); choose(matches[0].game_id) } else if (e.key === 'Escape') setTeamQuery('') }} />
        <p id="market-team-search-status" className="visually-hidden" role="status">{query ? (matches.length ? `${matches.length} matching game${matches.length === 1 ? '' : 's'}. Press Enter to choose the first.` : 'No matching games.') : ''}</p>
        {query ? <div className="market-game-results" role="group" aria-label="Matching games">
          {matches.length ? matches.slice(0, 12).map(g => <button key={g.game_id} type="button"
            aria-current={game.game_id === g.game_id ? 'true' : undefined}
            onClick={() => choose(g.game_id)}>
            {titleCase(g.game_id < 0 ? 'Your matchup' : `Week ${g.week}`)} · {g.away} {g.neutral_site ? 'vs.' : 'at'} {g.home}
          </button>) : <p>No matching games. Try another team name.</p>}
          {matches.length > 12 && <p>{matches.length} matches. Type more of the team name to narrow the list.</p>}
        </div> : <p className="market-selected-game">Selected game: {game.away} {game.neutral_site ? 'vs.' : 'at'} {game.home} ({game.game_id < 0 ? 'your hypothetical matchup' : `Week ${game.week}`})</p>}
        <button type="button" className="market-custom" onClick={onCustom}>Other Matchup</button>
      </div>
      <MarketCalculator key={`${game.game_id}|${game.home}|${game.away}`} headingLevel="h3" home={game.home} away={game.away}
        homeProbability={game.home_win_probability} homeMargin={game.home_margin} source={sourceFor(game)} />
      <details className="market-history" onToggle={e => setHistoryOpen((e.target as HTMLDetailsElement).open)}>
        <summary>Historical ATS and Over/Under Records for {game.away} and {game.home}</summary>
        {historyOpen && <MarketHistory teams={[game.away, game.home]} />}
      </details>
    </>}
  </section>
}

type Rate = { w?: number; l?: number; o?: number; u?: number; p: number; rate: number | null; ci95: [number, number] | null; sample: string; decided: number }
type Metrics = { generated_at?: string; attribution: string; teams: Record<string, { overall: { ats: Rate; ou: Rate } }> }

function MarketHistory({ teams }: { teams: string[] }) {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    fetch(import.meta.env.BASE_URL + 'v7-market-metrics.json', { signal: controller.signal })
      .then(r => { if (!r.ok) throw new Error(); return r.json() }).then(setMetrics).catch(() => { if (!controller.signal.aborted) setFailed(true) })
    return () => controller.abort()
  }, [])
  if (failed) return <p role="status">Historical records are unavailable right now.</p>
  if (!metrics) return <p role="status">Loading historical records…</p>
  const rate = (r: Rate) => r.rate == null ? `N/A (${r.sample} sample)` : `${(r.rate * 100).toFixed(1)}% (95% CI ${(r.ci95![0] * 100).toFixed(0)}–${(r.ci95![1] * 100).toFixed(0)}%)`
  return <div className="table-wrap">
    <p className="metric-note">Market archive last rebuilt: {metrics.generated_at && Number.isFinite(Date.parse(metrics.generated_at)) ? new Date(metrics.generated_at).toLocaleString() : 'unavailable'}. Market retrieval may be deferred to prioritize football results. These records can lag the latest scores; this is not a live betting feed.</p>
    <table>
      <caption>Records Against the Selected Provider's Closing Line, 2016 to Date. Pushes Excluded from Rates.</caption>
      <thead><tr><th scope="col">Team</th><th scope="col">ATS W-L-P</th><th scope="col">Cover Rate</th><th scope="col">O/U O-U-P</th><th scope="col">Over Rate</th></tr></thead>
      <tbody>{teams.map(team => { const t = metrics.teams[team]?.overall; return <tr key={team}><th scope="row">{team}</th>
        {t ? <><td>{t.ats.w}-{t.ats.l}-{t.ats.p}</td><td>{rate(t.ats)}</td><td>{t.ou.o}-{t.ou.u}-{t.ou.p}</td><td>{rate(t.ou)}</td></> : <td colSpan={4}>No closing-line history for this program.</td>}</tr> })}</tbody>
    </table>
    <small>Descriptive history, not a prediction. About 5% of teams show an interval excluding 50% by chance alone. {metrics.attribution}.</small>
  </div>
}
