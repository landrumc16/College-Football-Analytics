import { titleCase } from './titleCase'
import { useEffect, useMemo, useState } from 'react'
import SchoolSearch from './SchoolSearch'
import { disagreement, favourite, likelyRecord, pct, scoreLine, tiebreakNote, weeks, type DualProjections, type ModelKey, type ProjectedGame, type TeamProjection, type View } from './modelProjections'
import './model-projections.css'

const VIEWS: { id: View; label: string }[] = [{ id: 'compare', label: 'Compare' }, { id: 'standard', label: 'Standard' }, { id: 'momentum', label: 'Momentum' }]

export function useDualProjections() {
  const [data, setData] = useState<DualProjections | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'dual-projections.json', { cache: 'no-store' })
      .then(r => { if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw new Error('unavailable'); return r.json() })
      .then((d: DualProjections) => { if (!active) return; if (d?.games && d?.teams) setData(d); else setFailed(true) })
      .catch(() => { if (active) setFailed(true) })
    return () => { active = false }
  }, [])
  return { data, failed }
}

function ModelPanel({ g, k, data, large }: { g: ProjectedGame; k: ModelKey; data: DualProjections; large?: boolean }) {
  const f = favourite(g, k)
  return <div className={`mp-model${large ? ' mp-large' : ''}`}>
    <span className="mp-model-name">{titleCase(data.models[k].label)}</span>
    <strong className="mp-score">{scoreLine(g, k)}</strong>
    <span className="mp-prob"><b>{pct(f.probability)}</b> {f.team} win probability</span>
  </div>
}

function Why({ g, data }: { g: ProjectedGame; data: DualProjections }) {
  const e = disagreement(g, data)
  return <div className="mp-why-wrap">
    <p className="mp-why">{e.summary}</p>
    <details className="mp-calc"><summary>How This Is Calculated</summary><ul>{e.details.map(d => <li key={d}>{d}</li>)}</ul></details>
  </div>
}

/** Mobile record card: team heading, then one clearly separated summary per model in the current view. */
function TeamCard({ name, t, models, data, note }: { name: string; t: TeamProjection; models: ModelKey[]; data: DualProjections; note: string | null }) {
  return <li className="mp-team-card">
    <h4>{name}</h4>
    <p className="mp-sub">{t.wins}–{t.losses} now · {t.remaining} {t.remaining === 1 ? 'game' : 'games'} left</p>
    {models.map(k => { const r = likelyRecord(t, k); return <div className="mp-team-model" key={k}>
      <span className="mp-model-name">{titleCase(data.models[k].label)}</span>
      <dl>
        <div><dt>Expected Record</dt><dd>{t[k].expected_wins.toFixed(1)}–{t[k].expected_losses.toFixed(1)}</dd></div>
        <div><dt>Most Likely</dt><dd>{r.wins}–{r.losses} ({pct(r.probability)})</dd></div>
        <div><dt>Conference Title</dt><dd>{pct(t[k].conference_title)}</dd></div>
        <div><dt>CFP</dt><dd>{pct(t[k].cfp_field)}</dd></div>
      </dl>
    </div> })}
    {note && <p className="mp-note">{note}</p>}
  </li>
}

function GameCard({ g, view, data }: { g: ProjectedGame; view: View; data: DualProjections }) {
  const when = g.start_date ? new Date(g.start_date).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) : 'Date TBA'
  const official = g.official ? (g.official.home_win_probability >= 0.5 ? `${g.home} ${pct(g.official.home_win_probability)}` : `${g.away} ${pct(1 - g.official.home_win_probability)}`) : null
  return <li className="mp-game">
    <div className="mp-game-head"><strong>{g.away} {g.neutral_site ? 'vs' : 'at'} {g.home}</strong><span className="mp-muted">Week {g.week} · {when}{g.neutral_site ? ' · neutral site' : ''}</span></div>
    {view === 'compare'
      ? <div className="mp-models"><ModelPanel g={g} k="standard" data={data} /><ModelPanel g={g} k="momentum" data={data} /></div>
      : <ModelPanel g={g} k={view} data={data} large />}
    {view === 'compare' && <Why g={g} data={data} />}
    {official && <p className="mp-official">Official forecast: {official}</p>}
  </li>
}

export default function ModelProjections({ initialTeam = '', onTeam, onResearch }: { initialTeam?: string; onTeam?: (team: string) => void; onResearch?: () => void }) {
  const { data, failed } = useDualProjections()
  const [view, setView] = useState<View>('compare')
  const [team, setTeam] = useState(initialTeam)
  const [week, setWeek] = useState<number | 'all'>('all')
  const [showAllGames, setShowAllGames] = useState(false)
  const [showAllTeams, setShowAllTeams] = useState(false)
  const allWeeks = useMemo(() => data ? weeks(data) : [], [data])
  useEffect(() => { if (data && week === 'all' && allWeeks.length) setWeek(allWeeks[0]) }, [data])  // default: the next week
  if (failed) return <section className="notice"><h2>Model Projections</h2><p role="status">Model projections are not available right now. Try again later.</p></section>
  if (!data) return <section className="notice"><h2>Model Projections</h2><p role="status">Loading model projections…</p></section>
  const schools = Object.keys(data.teams).sort((a, b) => a.localeCompare(b))
  const games = data.games.filter(g => (week === 'all' || g.week === week) && (!team || g.home === team || g.away === team))
  const shownGames = showAllGames ? games : games.slice(0, 12)
  const sortKey: ModelKey = view === 'momentum' ? 'momentum' : 'standard'
  const teamRows = Object.entries(data.teams)
    .filter(([name]) => !team || name === team)
    .sort((a, b) => (b[1][sortKey].cfp_field ?? 0) - (a[1][sortKey].cfp_field ?? 0) || b[1][sortKey].expected_wins - a[1][sortKey].expected_wins || a[0].localeCompare(b[0]))
  const shownTeams = showAllTeams || team ? teamRows : teamRows.slice(0, 25)
  const models: ModelKey[] = view === 'compare' ? ['standard', 'momentum'] : [view]
  return <section className="notice model-projections" aria-labelledby="mp-title">
    <h2 id="mp-title">Model Projections</h2>
    <p className="page-deck">Two independent forecasts for every upcoming game. <strong>Standard</strong> counts every game equally; <strong>Momentum</strong> counts recent games more. Official forecasts are unchanged.</p>
    <p className="metric-note">Projection source receipt: {data.data_retrieved_at || 'unavailable'}. {(!data.data_retrieved_at || Date.now()-Date.parse(data.data_retrieved_at)>24*3600000) && 'This source is older than 24 hours or unavailable; it may not reflect the latest results.'}</p><div className="mp-controls">
      <fieldset className="mp-views"><legend>View</legend>
        {VIEWS.map(o => <label key={o.id}><input type="radio" name="mp-view" value={o.id} checked={view === o.id} onChange={() => setView(o.id)} />{titleCase(o.label)}</label>)}
      </fieldset>
      <label className="mp-week">Week <select aria-label="Week" value={String(week)} onChange={e => setWeek(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
        {allWeeks.map(w => <option key={w} value={w}>Week {w}</option>)}<option value="all">All Remaining Weeks</option></select></label>
      <SchoolSearch label="Find a Team" value={team} onChange={t => { setTeam(t); if (t) setWeek('all'); onTeam?.(t) }} schools={schools} />
    </div>
    {team && <p><button type="button" className="mp-link" onClick={() => setTeam('')}>Show Every Team</button></p>}
    <section aria-labelledby="mp-games-title"><h3 id="mp-games-title">Upcoming Games</h3>
      {games.length ? <ol className="mp-games">{shownGames.map(g => <GameCard key={g.game_id} g={g} view={view} data={data} />)}</ol>
        : <p role="status">No remaining games match this selection.</p>}
      {games.length > 12 && <button type="button" className="mp-more" onClick={() => setShowAllGames(!showAllGames)}>{titleCase(showAllGames ? 'Show fewer games' : `Show all ${games.length} games`)}</button>}
    </section>
    <section aria-labelledby="mp-records-title"><h3 id="mp-records-title">Projected Records and Playoff Odds</h3>
      <p className="mp-muted">Each model's record and odds come from its own game probabilities; conference and CFP odds use the existing playoff simulation rules.</p>
      <ul className="mp-team-cards" aria-label={`Projected records: ${view === 'compare' ? 'Standard and Momentum' : data.models[view].label}`}>
        {shownTeams.map(([name, t]) => <TeamCard key={name} name={name} t={t} models={models} data={data} note={view === 'compare' ? tiebreakNote(name, t) : null} />)}
      </ul>
      <div className="table-wrap mp-records-wrap"><table className="mp-table mp-records">
        <caption>{view === 'compare' ? 'Standard and Momentum' : data.models[view].label} · Sorted by CFP Chance</caption>
        <thead><tr><th scope="col">Team</th>{models.map(k => <th scope="col" key={k}>{titleCase(data.models[k].label)}</th>)}</tr></thead>
        <tbody>{shownTeams.map(([name, t]) => <tr key={name}>
          <th scope="row">{name}<small className="mp-sub">{t.wins}–{t.losses} now · {t.remaining} left</small>{view === 'compare' && tiebreakNote(name, t) && <small className="mp-sub mp-note">{tiebreakNote(name, t)}</small>}</th>
          {models.map(k => { const r = likelyRecord(t, k); return <td key={k}>
            <b>{t[k].expected_wins.toFixed(1)}–{t[k].expected_losses.toFixed(1)}</b><small className="mp-sub">most likely <span className="mp-nowrap">{r.wins}–{r.losses} ({pct(r.probability)})</span></small>
            <small className="mp-sub"><span className="mp-nowrap">CFP {pct(t[k].cfp_field)}</span> · <span className="mp-nowrap">conf. title {pct(t[k].conference_title)}</span></small></td> })}
        </tr>)}</tbody>
      </table></div>
      {!team && teamRows.length > 25 && <button type="button" className="mp-more" onClick={() => setShowAllTeams(!showAllTeams)}>{titleCase(showAllTeams ? 'Show top 25' : `Show all ${teamRows.length} teams`)}</button>}
    </section>
    <details className="mp-more-info"><summary>How the Models Work and How Accurate They Have Been</summary>
      <ul>
        <li><strong>Standard:</strong> {data.models.standard.weighting}.</li>
        <li><strong>Momentum:</strong> {data.models.momentum.weighting}.</li>
        {Object.entries(data.method).map(([k, text]) => <li key={k}><strong>{k[0].toUpperCase() + k.slice(1)}:</strong> {text}.</li>)}
      </ul>
      {onResearch && <button type="button" onClick={onResearch}>Model Accountability in Research</button>}
    </details>
  </section>
}

export function HistoricalModelValidation() {
  const {data,failed}=useDualProjections()
  if(!data)return <p role="status">{failed?'Historical model evidence is unavailable.':'Loading historical model evidence…'}</p>
  const v=data.validation
  const brier=(block:Record<string,{brier:number}>,key:string)=>block[key]?.brier.toFixed(4)??'N/A'
  return <details className="mp-more-info"><summary>Historical Model Comparisons · Replays</summary><p>These historical studies are separate from retained pregame accountability. They do not authorize changing the official model.</p>      <div className="table-wrap"><table className="mp-table mp-validation">
        <caption>Historical Accuracy on Identical Games (Brier Score: Lower Is Better)</caption>
        <thead><tr><th scope="col">Games</th><th scope="col">Standard</th><th scope="col">Momentum</th><th scope="col">Existing Method*</th></tr></thead>
        <tbody>
          <tr><th scope="row">2017–2025 ({v.games.toLocaleString()})</th><td>{brier(v.pooled_2017_2025, 'standard')}</td><td>{brier(v.pooled_2017_2025, 'momentum')}</td><td>{brier(v.pooled_2017_2025, 'incumbent_replay')}</td></tr>
          <tr><th scope="row">Second Half of Seasons</th><td>{brier(v.second_half, 'standard')}</td><td>{brier(v.second_half, 'momentum')}</td><td>{brier(v.second_half, 'incumbent_replay')}</td></tr>
          <tr><th scope="row">Held-out 2022–2025 ({v.test_games.toLocaleString()})</th><td>{brier(v.test_2022_2025, 'standard')}</td><td>{brier(v.test_2022_2025, 'momentum')}</td><td>{brier(v.test_2022_2025, 'incumbent_replay')}</td></tr>
          <tr><th scope="row">2026 Mixed-Evidence Study ({v.authentic_2026_games})</th><td>{v.authentic_2026.standard?.toFixed(4)}</td><td>{v.authentic_2026.momentum?.toFixed(4)}</td><td>{v.authentic_2026.published_incumbent?.toFixed(4)} (published)</td></tr>
        </tbody>
      </table></div>
      <p className="mp-muted">*Historical rows replay the existing rating method with last season's rating as its starting point; they are not archived forecasts. In the 2026 row only the existing-method probabilities were archived before kickoff; Standard and Momentum were retrospectively computed from pre-week data. This row is not a three-model authentic pregame comparison. Projected-record error at mid-season: Standard {v.season_records_mae_wins.standard} wins, Momentum {v.season_records_mae_wins.momentum}, existing method {v.season_records_mae_wins.incumbent_replay}. Data retrieved {data.data_retrieved_at ? new Date(data.data_retrieved_at).toLocaleString() : 'N/A'}.</p>
</details>
}
