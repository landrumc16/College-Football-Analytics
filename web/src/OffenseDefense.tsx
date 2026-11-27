import { eligibleSchool } from './favoriteDefaults'
import { useFavoriteSelection } from './FavoriteDefaults'
import { titleCase } from './titleCase'
import { useEffect, useMemo, useState } from 'react'
import SchoolSearch from './SchoolSearch'
import { advantageLabel, edgeStrength, explainEdge, field, shortReason, format, GROUPS, leaderboard, lowerIsBetter, matchupEdges, notableEdges, percentile, poolSize, sampleUnit,
  type Side, type V8Stats, type View } from './v8Stats'
import './offense-defense.css'

const VIEWS: { id: View; label: string; short: string; help: string }[] = [
  { id: 'raw', label: 'Traditional', short: 'Every game, as played.', help: 'Every game played, including FCS opponents. Not adjusted for opponents.' },
  { id: 'power', label: 'Power Four Only', short: 'Only games against power-conference opponents.', help: 'Only games against ACC, Big Ten, Big 12, SEC and Notre Dame opponents. Shown for power-conference teams.' },
  { id: 'adjusted', label: 'Opponent-Adjusted', short: 'Rated against an average FBS opponent.', help: 'Expected result against an average FBS opponent on a neutral field. Accounts for every opponent once; small samples are pulled toward average.' },
]

export function useV8Stats() {
  const [data, setData] = useState<V8Stats | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v8-team-stats.json', { cache: 'no-store' })
      .then(r => { if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw new Error('unavailable'); return r.json() })
      .then((d: V8Stats) => { if (!active) return; if (d?.teams && Object.keys(d.teams).length) setData(d); else setFailed(true) })
      .catch(() => { if (active) setFailed(true) })
    return () => { active = false }
  }, [])
  return { data, failed }
}

function Rank({ rank, pool }: { rank: number | null; pool: number }) {
  if (rank == null) return <span className="od-muted">—</span>
  const p = percentile(rank, pool)
  return <span className={p != null && p >= 80 ? 'od-rank od-good' : p != null && p <= 20 ? 'od-rank od-weak' : 'od-rank'}>#{rank}<small> of {pool}</small></span>
}

// Sacks, run stuffs and turnovers run against intuition on both sides (lower is better on offense, higher on defense).
const unusualDirection = (metric: string, _side: Side) => ['sack', 'stuff', 'to'].includes(metric)

function UnitRows({ data, team, side, view, groups }: { data: V8Stats; team: string; side: Side; view: View; groups: typeof GROUPS }) {
  const t = data.teams[team]
  const pool = poolSize(data, view)
  return <>
    <thead><tr><th scope="col">Measure</th><th scope="col">{titleCase(side === 'offense' ? 'Gained' : 'Allowed')}</th><th scope="col">{titleCase(view === 'power' ? 'Power rank' : 'FBS rank')} <span className="od-head-note">(#1 best)</span></th></tr></thead>
    {groups.map(group => <tbody key={group.id}>
      <tr className="od-group"><th scope="rowgroup" colSpan={3}>{titleCase(group.label)}</th></tr>
      {group.metrics.map(metric => {
        const row = t[side][metric], f = field(row, view)
        const n = view === 'power' ? (f.games != null ? `${f.games} games` : '—') : row?.[8] != null ? `${Math.round(row[8] as number)} ${sampleUnit(metric)}` : '—'
        return <tr key={metric}>
          <th scope="row">{titleCase(data.definitions[metric].label)}{unusualDirection(metric, side) && <small className="od-muted"> ({lowerIsBetter(data.definitions, metric, side) ? 'lower' : 'higher'} is better)</small>}<small className="od-sample">{n}</small></th>
          <td>{format(metric, f.value)}{view === 'adjusted' && f.se != null && f.value != null && <small className="od-muted"> ± {format(metric, 1.645 * f.se).replace('%', '')}</small>}</td>
          <td><Rank rank={f.rank} pool={pool} /></td>
        </tr>
      })}
    </tbody>)}
  </>
}

/** Scoring and efficiency always visible; running, passing and situational detail one tap away. */
function UnitTable({ data, team, side, view }: { data: V8Stats; team: string; side: Side; view: View }) {
  const unit = side === 'offense' ? 'Offense' : 'Defense'
  return <div className="od-unit">
    <div className="table-wrap"><table className="od-table">
      <caption>{unit} · {VIEWS.find(v => v.id === view)!.label}</caption>
      <UnitRows data={data} team={team} side={side} view={view} groups={GROUPS.slice(0, 1)} />
    </table></div>
    <details className="od-more od-unit-more"><summary>{unit}: Running, Passing and Situational</summary>
      <div className="table-wrap"><table className="od-table">
        <caption>{unit} Detail · {VIEWS.find(v => v.id === view)!.label}</caption>
        <UnitRows data={data} team={team} side={side} view={view} groups={GROUPS.slice(1)} />
      </table></div>
    </details>
  </div>
}

function Trends({ data, team }: { data: V8Stats; team: string }) {
  const t = data.teams[team]
  const items: [string, string][] = [['offense_epa', 'Offense efficiency'], ['offense_ppd', 'Offense scoring'], ['defense_epa', 'Defense efficiency'], ['defense_ppd', 'Defense scoring']]
  return <section className="od-card" aria-labelledby="od-trends"><h3 id="od-trends">Recent Form and Consistency</h3>
    <p className="od-muted">Last 4 games vs earlier games, adjusted for opponents. Labelled only when the change is bigger than its uncertainty.</p>
    <ul className="od-trends">{items.map(([key, label]) => {
      const tr = t.trend[key], vol = t.volatility[key]
      return <li key={key}><strong>{titleCase(label)}</strong>
        <span className={`od-badge ${tr?.label ?? 'none'}`}>{tr ? (tr.label === 'improving' ? '▲ Improving' : tr.label === 'declining' ? '▼ Declining' : '● Steady') : 'Not enough games'}</span>
        <small className="od-muted">{vol ? `Game-to-game swing: ${vol.sd.toFixed(2)} over ${vol.games} games (lower = more consistent)` : 'Consistency needs 5+ games'}</small></li>
    })}</ul>
  </section>
}

function Matchup({ data, team, opponent }: { data: V8Stats; team: string; opponent: string }) {
  const edges = matchupEdges(data, team, opponent)
  const top = notableEdges(edges, 3)
  const rows = (offense: string) => edges.filter(e => e.offense === offense)
  return <section className="od-matchup" aria-labelledby="od-matchup"><h3 id="od-matchup">How {team} and {opponent} Match Up</h3>
    <p className="od-muted">The strongest edges when each offense meets the other defense. Descriptive only: game predictions do not change.</p>
    {top.length ? <ol className="od-edge-cards" aria-label="Biggest matchup advantages">{top.map(e => <li key={e.offense + e.metric}>
      <span className="od-edge-kicker">{advantageLabel(e)}</span>
      <strong className="od-edge-title">{titleCase(e.label)}</strong>
      <span className="od-edge-stat"><b>{format(e.metric, e.expected)}</b> expected vs {format(e.metric, e.mean)} national average</span>
      <p>{shortReason(e)}</p>
      <details className="od-calc"><summary>How This Is Calculated</summary>
        <p>{explainEdge(e)} {edgeStrength(e)}: {Math.abs(e.size).toFixed(1)} national standard deviations from average (an edge needs at least 0.5; 1.0 or more is clear).</p>
      </details>
    </li>)}</ol>
      : <p>No phase of this matchup stands out: every expected value is within half a standard deviation of the national average.</p>}
    <details className="od-more"><summary>All Matchup Factors</summary>
      <p className="od-muted">Expected = one team's opponent-adjusted offense combined with the other's opponent-adjusted defense on a neutral field. An edge needs half a national standard deviation or more.</p>
      {[team, opponent].map(offense => <div className="table-wrap" key={offense}><table className="od-table">
        <caption>{offense} Offense vs {offense === team ? opponent : team} Defense</caption>
        <thead><tr><th scope="col">Phase</th><th scope="col">Expected</th><th scope="col"><abbr title="National average">Nat. avg</abbr></th><th scope="col">Edge</th></tr></thead>
        <tbody>{rows(offense).map(e => <tr key={e.metric}><th scope="row">{titleCase(e.label)}</th><td>{format(e.metric, e.expected)}</td><td>{format(e.metric, e.mean)}</td>
          <td><span className={Math.abs(e.size) >= 0.5 ? (e.size > 0 ? 'od-rank od-good' : 'od-rank od-weak') : 'od-muted'}>{Math.abs(e.size) < 0.5 ? 'Even' : e.size > 0 ? 'Offense' : 'Defense'}</span></td></tr>)}</tbody>
      </table></div>)}
    </details>
  </section>
}

export default function OffenseDefense({ team, onTeam, onProfile, initialOpponent = '', showLeaders = false }: { team: string; onTeam: (team: string) => void; onProfile: (team: string) => void; initialOpponent?: string; showLeaders?: boolean }) {
  const { data, failed } = useV8Stats()
  const [view, setView] = useState<View>('adjusted')
  const [boardMetric, setBoardMetric] = useState('epa')
  const [boardSide, setBoardSide] = useState<Side>('offense')
  const [showAll, setShowAll] = useState(false)
  const [opponent,setOpponent]=useFavoriteSelection({scope:'statistics-opponent',eligible:data?Object.keys(data.teams).filter(t=>t!==(eligibleSchool(team,Object.keys(data.teams))??team)):[],initial:initialOpponent})
  const [leadersOpen, setLeadersOpen] = useState(() => showLeaders || !window.matchMedia('(max-width: 767px)').matches)
  const jump = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  // Arriving from Rankings: open the national leaders and bring them into view once the data has loaded.
  useEffect(() => { if (showLeaders && data) document.getElementById('od-board-section')?.scrollIntoView({ block: 'start' }) }, [showLeaders, data])
  const schools = useMemo(() => data ? Object.keys(data.teams).sort((a, b) => a.localeCompare(b)) : [], [data])
  if (failed) return <section className="notice"><h2>Offense &amp; Defense</h2><p role="status">Offense and defense statistics are not available right now. Try again later.</p></section>
  if (!data) return <section className="notice"><h2>Offense &amp; Defense</h2><p role="status">Loading offense and defense statistics…</p></section>
  const selected = eligibleSchool(team,schools) ?? ''
  const t = selected ? data.teams[selected] : null
  const powerViewUnavailable = view === 'power' && t && !t.power
  const board = leaderboard(data, boardMetric, boardSide, view)
  return <section className="notice offense-defense" aria-labelledby="od-title">
    <h2 id="od-title">Offense &amp; Defense</h2>
    <p className="page-deck">How every FBS offense and defense performed. {data.season} season{data.coverage ? ` · ${data.coverage.games_with_plays} of ${data.coverage.completed_games} games with play-by-play` : ''}.</p>
    <div className="od-controls">
      <SchoolSearch label="Choose Team" value={selected} onChange={onTeam} schools={schools} />
      <fieldset className="od-views"><legend>Statistics</legend>
        {VIEWS.map(v => <label key={v.id}><input type="radio" name="od-view" value={v.id} checked={view === v.id} onChange={() => setView(v.id)} />{titleCase(v.label)}</label>)}
      </fieldset>
    </div>
    <p className="od-muted od-help">{VIEWS.find(v => v.id === view)!.short}</p>
    <details className="od-more od-guide"><summary>How to Read These Numbers</summary>
      <ul>
        {VIEWS.map(v => <li key={v.id}><strong>{titleCase(v.label)}:</strong> {v.help}</li>)}
        <li><strong>Rank:</strong> #1 is always the best, whichever way the numbers run. Offense ranks reward more; defense ranks reward allowing less, except sacks, run stuffs and turnovers, where the note in the row says which way is better.</li>
        <li><strong>± range:</strong> opponent-adjusted values show a 90% range. For example 0.15 ± 0.08 means the team's true level is very likely between 0.07 and 0.23. Bigger samples give narrower ranges.</li>
        <li><strong>Sample:</strong> the small grey line under each measure is how many plays, drives, attempts or games the number is based on.</li>
        <li><strong>Descriptive, not predictive:</strong> these statistics describe how units performed. Game predictions still come from the existing model.</li>
      </ul>
    </details>
    {t && <>
      <nav className="od-jump" aria-label="On this page">
        <button type="button" onClick={() => jump('od-stats')}>Statistics</button>
        <button type="button" onClick={() => jump('od-vs')}>Matchup</button>
        <button type="button" onClick={() => jump('od-trends')}>Recent Form</button>
        <button type="button" onClick={() => { setLeadersOpen(true); setTimeout(() => jump('od-board-section'), 0) }}>Leaders</button>
        <button type="button" onClick={() => onProfile(selected)}>Team Profile</button>
      </nav>
      <div className="od-summary" aria-label={`${selected} summary`}>
        <div><small>Record Context</small><strong>{t.games} games</strong><span className="od-muted">{t.power_games} vs power opponents · {t.fcs_games} vs FCS</span></div>
        <div><small>Points per Game</small><strong>{t.ppg?.toFixed(1) ?? 'N/A'}</strong><span className="od-muted">allowed {t.papg?.toFixed(1) ?? 'N/A'}</span></div>
        <div><small>Conference</small><strong>{t.conference ?? 'N/A'}</strong><span className="od-muted">{t.power ? 'Power conference' : 'Not a power conference'}</span></div>
      </div>
      {powerViewUnavailable ? <p role="status">{selected} is not in a power conference, so the Power Four-only view does not apply. Its opponent-adjusted numbers compare it with every FBS team.</p>
        : <div className="od-units" id="od-stats"><UnitTable data={data} team={selected} side="offense" view={view} /><UnitTable data={data} team={selected} side="defense" view={view} /></div>}
      <section className="od-card" aria-labelledby="od-vs"><h3 id="od-vs">Compare a Matchup</h3>
        <SchoolSearch label="Choose Opponent" value={opponent} onChange={setOpponent} schools={schools.filter(s => s !== selected)} />
        {opponent && data.teams[opponent] && <Matchup data={data} team={selected} opponent={opponent} />}
      </section>
      <Trends data={data} team={selected} />
    </>}
    {!t && <p role="status">Choose a team to see its offense and defense, or browse the leaders below.</p>}
    <details className="od-card od-leaders" id="od-board-section" open={leadersOpen} onToggle={e => setLeadersOpen((e.currentTarget as HTMLDetailsElement).open)}>
      <summary><h3 id="od-board">National Leaders</h3></summary>
      <div className="od-board-controls">
        <label>Measure <select value={boardMetric} onChange={e => setBoardMetric(e.target.value)}>{GROUPS.map(g => <optgroup key={g.id} label={g.label}>{g.metrics.map(m => <option key={m} value={m}>{titleCase(data.definitions[m].label)}</option>)}</optgroup>)}</select></label>
        <label>Unit <select value={boardSide} onChange={e => setBoardSide(e.target.value as Side)}><option value="offense">Offense</option><option value="defense">Defense</option></select></label>
      </div>
      <div className="table-wrap"><table className="od-table od-board-table">
        <caption>{titleCase(boardSide === 'offense' ? 'Offense' : 'Defense')}: {titleCase(data.definitions[boardMetric].label)} · {VIEWS.find(v => v.id === view)!.label}{titleCase(lowerIsBetter(data.definitions, boardMetric, boardSide) ? ' (lower is better)' : '')}</caption>
        <colgroup><col className="od-col-rank" /><col /><col className="od-col-value" /></colgroup>
        <thead><tr><th scope="col">Rank</th><th scope="col">Team</th><th scope="col">Value</th></tr></thead>
        <tbody>{(showAll ? board : board.slice(0, 25)).map(row => <tr key={row.team} className={row.team === selected ? 'selected-row' : undefined}>
          <td>{row.rank}</td><td><button type="button" className="od-team" onClick={() => onTeam(row.team)}>{row.team}</button><small className="od-muted od-conf">{row.conference}</small></td>
          <td>{format(boardMetric, row.value)}{view === 'power' && row.games != null && <small className="od-muted"> · {row.games} g</small>}</td></tr>)}</tbody>
      </table></div>
      {board.length > 25 && <button type="button" onClick={() => setShowAll(!showAll)}>{titleCase(showAll ? 'Show top 25' : `Show all ${board.length}`)}</button>}
    </details>
    <details className="od-card"><summary>How These Numbers Work</summary>
      <ul>{Object.entries(data.method).map(([k, v]) => <li key={k}><strong>{titleCase(k.replaceAll('_', ' '))}:</strong> {v}</li>)}</ul>
      <p className="od-muted">Source: {data.source}. Rates use plays from scrimmage; penalties, kicks and kneel-downs are not plays. Expected points added comes from the provider's play-level model. N/A means the measure cannot be calculated reliably from the available data.</p>
    </details>
  </section>
}
