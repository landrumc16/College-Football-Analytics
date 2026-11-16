import { useEffect, useState } from 'react'
import MarketCalculator, { type ModelSource } from './MarketCalculator'

export type MarketGame = { game_id: number; week: number; home: string; away: string; neutral_site?: boolean; home_margin: number; home_win_probability: number }
type Props = { games: MarketGame[]; selectedId: number | null; onSelect: (id: number) => void; onCustom: () => void; sourceFor: (game: MarketGame) => ModelSource }

// The Market Analysis page: pick a game, enter a market number, read the comparison. History is secondary and lazy.
export default function MarketAnalysis({ games, selectedId, onSelect, onCustom, sourceFor }: Props) {
  const game = games.find(g => g.game_id === selectedId) ?? games[0]
  const [historyOpen, setHistoryOpen] = useState(false)
  return <section className="market-analysis" aria-labelledby="market-analysis-title">
    <h2 id="market-analysis-title">Market Analysis</h2>
    <p className="page-deck">Pick a game, type the spread, probability or moneyline you see, and compare it with our model instantly. Educational only: not betting advice.</p>
    {!game ? <div className="notice"><p>No upcoming FBS-vs-FBS game has a published forecast right now.</p><button type="button" onClick={onCustom}>Compare any two schools</button></div> : <>
      <div className="market-game-row">
        <label htmlFor="market-game">Game</label>
        <select id="market-game" value={game.game_id} onChange={e => onSelect(Number(e.target.value))}>
          {games.map(g => <option key={g.game_id} value={g.game_id}>{`${g.game_id < 0 ? 'Your matchup (hypothetical)' : `Week ${g.week}`} · ${g.away} ${g.neutral_site ? 'vs.' : 'at'} ${g.home}`}</option>)}
        </select>
        <button type="button" className="market-custom" onClick={onCustom}>Other matchup</button>
      </div>
      <MarketCalculator key={`${game.game_id}|${game.home}|${game.away}`} headingLevel="h3" home={game.home} away={game.away}
        homeProbability={game.home_win_probability} homeMargin={game.home_margin} source={sourceFor(game)} />
      <details className="market-history" onToggle={e => setHistoryOpen((e.target as HTMLDetailsElement).open)}>
        <summary>Historical ATS and over/under records for {game.away} and {game.home}</summary>
        {historyOpen && <MarketHistory teams={[game.away, game.home]} />}
      </details>
    </>}
  </section>
}

type Rate = { w?: number; l?: number; o?: number; u?: number; p: number; rate: number | null; ci95: [number, number] | null; sample: string; decided: number }
type Metrics = { attribution: string; teams: Record<string, { overall: { ats: Rate; ou: Rate } }> }

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
    <table>
      <caption>Records against the selected provider's closing line, 2016 to date. Pushes excluded from rates.</caption>
      <thead><tr><th scope="col">Team</th><th scope="col">ATS W-L-P</th><th scope="col">Cover rate</th><th scope="col">O/U O-U-P</th><th scope="col">Over rate</th></tr></thead>
      <tbody>{teams.map(team => { const t = metrics.teams[team]?.overall; return <tr key={team}><th scope="row">{team}</th>
        {t ? <><td>{t.ats.w}-{t.ats.l}-{t.ats.p}</td><td>{rate(t.ats)}</td><td>{t.ou.o}-{t.ou.u}-{t.ou.p}</td><td>{rate(t.ou)}</td></> : <td colSpan={4}>No closing-line history for this program.</td>}</tr> })}</tbody>
    </table>
    <small>Descriptive history, not a prediction. About 5% of teams show an interval excluding 50% by chance alone. {metrics.attribution}.</small>
  </div>
}
