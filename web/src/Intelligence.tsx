import { useFavoriteSelection } from './FavoriteDefaults'
import { titleCase } from './titleCase'
import { useEffect, useState } from 'react'
import { StatExplain, Takeaway } from './StatExplain'
import SchoolSearch from './SchoolSearch'
import type { IntelligenceMetric, IntelligenceFinding } from './teamIntelligenceContract'
import './intelligence.css'

type Trend = { recent: number; season: number; change: number; label: string; games: number }
export type TeamIntelligence = {
  team: string; accomplishment: { wins: number; losses: number }; strength: IntelligenceMetric;
  current_level: IntelligenceMetric; schedule: IntelligenceMetric;
  units: { offense: IntelligenceMetric; defense: IntelligenceMetric };
  trends: Record<string, IntelligenceMetric<Trend> & { actual_window: number | null }>;
  findings: IntelligenceFinding[];
}
type Observation = { report_generated_at: string; retained_at: string; source_sha256: string; teams: {team: string;rating: number;rank: number}[] }
type Payload = { schema_version: number; season: number; teams: TeamIntelligence[]; observations: Observation[] }
let pending: Promise<Payload> | undefined
export function useIntelligence() {
  const [data, setData] = useState<Payload | null>(null)
  const [status, setStatus] = useState('Loading intelligence…')
  useEffect(() => {
    pending ??= fetch(import.meta.env.BASE_URL + 'team-intelligence.json', {cache:'no-store'}).then(async r => {
      if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw Error('Not published')
      const p = await r.json()
      if (p.schema_version !== 1 || !Array.isArray(p.teams) || !p.teams.every((t: TeamIntelligence) => t.team && t.strength && t.units && t.findings)) throw Error('Invalid contract')
      return p as Payload
    })
    let active = true
    pending.then(p => { if (active) {setData(p);setStatus('')} }).catch(() => {if(active) setStatus('Intelligence is not published. Existing team data remains available.'); pending = undefined})
    return () => {active = false}
  }, [])
  return {data, status}
}
export function metricNumber(metric: IntelligenceMetric | undefined, digits = 1) {
  return metric?.status === 'available' && typeof metric.value === 'number' && Number.isFinite(metric.value) ? metric.value.toFixed(digits) : 'Unavailable'
}
function Evidence({metric}: {metric: IntelligenceMetric<unknown>}) {
  return <StatExplain label="Evidence, Freshness & Limitations"><p>{metric.units} · {metric.population} · sample {metric.sample ?? 'not supplied'}.</p><p>Source: {metric.source} · source receipt {metric.source_receipt ?? 'unavailable'} · {metric.freshness.status} at artifact build. This is source age, not a promised refresh interval.</p>{metric.limitations.map(l => <p key={l}>{l}</p>)}</StatExplain>
}
export function IntelligenceBrief({team, onOpen}: {team: string;onOpen: () => void}) {
  const {data} = useIntelligence(); const t = data?.teams.find(t => t.team === team)
  if (!t) return null
  return <div className="intelligence-brief"><p><strong>{team}</strong> · season strength {metricNumber(t.strength)} · last-three level {metricNumber(t.current_level)}.</p><p>A recent sample describes current performance; it does not change our official forecast.</p><button onClick={onOpen}>Understand This Team</button></div>
}
export function IntelligenceProfile({team}: {team: string}) {
  const {data,status} = useIntelligence(); const t = data?.teams.find(t=>t.team === team)
  const [point, setPoint] = useState(0)
  if (!t) return <p role="status">{status || 'No intelligence available for this school.'}</p>
  const observations = (data?.observations ?? []).map(o=>({...o, row:o.teams.find(r=>r.team===team)})).filter(o=>o.row).sort((a,b)=>a.report_generated_at.localeCompare(b.report_generated_at))
  const selected = observations[Math.min(point,Math.max(0,observations.length-1))]
  const values = observations.map(o=>o.row!.rating); const min = Math.min(...values)-1; const max = Math.max(...values)+1
  return <section className="intelligence-profile" aria-label={`${team} intelligence`}><h3>Understand This Team</h3>
    <p className="page-deck">Report receipt {t.strength.source_receipt ?? 'unavailable'} · unit-statistics receipt {t.units.offense.source_receipt ?? 'unavailable'}. Source-age status below was measured when this artifact was built.</p><Takeaway>{t.findings.find(f=>f.id === 'current-level')?.takeaway || t.findings[0]?.takeaway || 'Not enough evidence for a conclusion.'}</Takeaway>
    <div className="team-profile-grid">{[['Earned record',`${t.accomplishment.wins}–${t.accomplishment.losses}`],['Season strength',metricNumber(t.strength)],['Last-three playing level',metricNumber(t.current_level)],['Rated schedule strength',metricNumber(t.schedule)]].map(([name,value])=><div className="team-profile-tile" key={name}><small>{titleCase(name)}</small><strong>{value}</strong></div>)}</div>
    <StatExplain label="Three Perspectives, Different Questions"><p>Record describes results earned. A national accomplishment score is not validated and is not ranked. Season strength is the existing model rating. Current level reuses the released last-three-game calculation with current opponent ratings; it is not an archived weekly observation or a replacement forecast.</p><p>Schedule context averages {t.schedule.sample ?? 0} rated completed opponents and excludes FCS/unrated opponents. No extra conference multiplier is applied.</p></StatExplain>
    <details className="profile-more"><summary>Offense, Defense & Recent Trends</summary><Takeaway>Offense benefits from higher adjusted EPA; defense benefits from allowing less. Short-window changes do not establish their cause.</Takeaway><div className="team-profile-grid">{(['offense','defense'] as const).map(side=><div className="team-profile-tile" key={side}><small>Opponent-Adjusted {titleCase(side)}</small><strong>{metricNumber(t.units[side],3)} EPA/play</strong><Evidence metric={t.units[side]}/>{t.trends[`${side}_epa`]?.value && <><p>Last {t.trends[`${side}_epa`].actual_window} eligible games: {t.trends[`${side}_epa`].value!.recent.toFixed(3)} · season {t.trends[`${side}_epa`].value!.season.toFixed(3)} · {t.trends[`${side}_epa`].value!.label}.</p><Evidence metric={t.trends[`${side}_epa`]}/></>}</div>)}</div></details>
    <details className="profile-more"><summary>Team Trajectory · Retained Observations</summary><Takeaway>{observations.length < 2 ? 'One observation cannot establish a trend. Earlier unarchived ratings are unavailable.' : 'These are retained model observations, not a reconstructed season.'}</Takeaway>{selected && <><p>{selected.report_generated_at}: strength <strong>{selected.row!.rating.toFixed(1)}</strong>, published model rank <strong>#{selected.row!.rank}</strong>.</p><svg className="intelligence-chart" viewBox="0 0 600 160" role="img" aria-label={`${team}: ${observations.length} retained strength observations`}><line x1="30" x2="570" y1="140" y2="140" stroke="currentColor"/><polyline points={observations.map((o,i)=>`${30+(observations.length>1?i/(observations.length-1):.5)*540},${130-(o.row!.rating-min)/(max-min)*110}`).join(' ')} fill="none" stroke="currentColor" strokeWidth="3"/>{observations.map((o,i)=><circle key={o.source_sha256} cx={30+(observations.length>1?i/(observations.length-1):.5)*540} cy={130-(o.row!.rating-min)/(max-min)*110} r="5" fill="currentColor"/>)}</svg><label>Inspect Retained Observation <select value={Math.min(point,observations.length-1)} onChange={e=>setPoint(Number(e.target.value))}>{observations.map((o,i)=><option value={i} key={o.source_sha256}>{o.report_generated_at}</option>)}</select></label><StatExplain label="Trajectory Sources & Interpretation"><p>Selected source SHA-256: {selected.source_sha256}. Retained {selected.retained_at}. Rank includes projected wins and is not a pure strength ranking. A source report timestamp is not proof of its public release time.</p></StatExplain></>}{!selected && <p>No retained observations published.</p>}</details>
    <StatExplain label="Supporting Findings & Source Receipts">{t.findings.map(f=><div key={f.id}><p><strong>{f.takeaway}</strong> {f.explanation}</p><small>Rule {f.id} v{f.rule_version} · {f.evidence_paths.join(', ')} · {f.source_receipt ?? 'receipt unavailable'}</small></div>)}<Evidence metric={t.strength}/><Evidence metric={t.current_level}/><Evidence metric={t.schedule}/></StatExplain>
  </section>
}
export function IntelligenceRankings({onTeam}: {onTeam:(team:string)=>void}) {
  const {data,status}=useIntelligence(); const [measure,setMeasure]=useState('strength'); const [search,setSearch]=useFavoriteSelection({scope:'intelligence-school',eligible:(data?.teams??[]).map(t=>t.team)})
  const labels: Record<string,string>={strength:'Underlying strength',current_level:'Current playing level · last three',offense:'Opponent-adjusted offense',defense:'Opponent-adjusted defense',schedule:'Played schedule context',accomplishment:'Season accomplishment · record only'}
  const metric=(t:TeamIntelligence)=>measure==='offense'||measure==='defense'?t.units[measure]:t[measure as 'strength'|'current_level'|'schedule']
  const rows=(data?.teams??[]).filter(t=>!search||t.team===search).slice().sort((a,b)=>measure==='accomplishment'?a.team.localeCompare(b.team):((metric(a)?.value ?? (measure==='defense'?Infinity:-Infinity))-(metric(b)?.value ?? (measure==='defense'?Infinity:-Infinity)))*(measure==='defense'?1:-1))
  return <section className="notice"><h2>National Intelligence</h2><Takeaway>{measure==='accomplishment'?'Records show what teams earned. A new national accomplishment ranking remains withheld pending validation.':measure==='defense'?'Lower adjusted EPA allowed describes stronger defensive efficiency.':'Compare one clearly named measure at a time. These views do not replace the official model ranking below.'}</Takeaway><div className="profile-tools"><label>Evaluation <select value={measure} onChange={e=>setMeasure(e.target.value)}>{Object.entries(labels).map(([value,label])=><option key={value} value={value}>{titleCase(label)}</option>)}</select></label><SchoolSearch label="Find School in Intelligence" value={search} onChange={setSearch} schools={(data?.teams??[]).map(t=>t.team).sort()}/><button onClick={()=>setSearch('')}>All Schools</button></div>{status&&<p role="status">{status}</p>}<details className="profile-more"><summary>{titleCase(labels[measure])} · {rows.length} Schools</summary><div className="table-wrap"><table><thead><tr><th>School</th><th>{titleCase(measure==='accomplishment'?'Record':'Value')}</th><th>Evidence</th></tr></thead><tbody>{rows.map(t=><tr key={t.team}><td><button onClick={()=>onTeam(t.team)}>{t.team}</button></td><td>{measure==='accomplishment'?`${t.accomplishment.wins}–${t.accomplishment.losses}`:`${metricNumber(metric(t),measure==='offense'||measure==='defense'?3:1)} ${metric(t)?.units??''}`}</td><td>{measure!=='accomplishment'&&<Evidence metric={metric(t)}/>}</td></tr>)}</tbody></table></div></details><StatExplain><p>Current level uses three completed games. Unit trends on team profiles prefer four eligible games with an explicit three-game fallback. Opponent adjustment is inherited from the existing statistics publisher. Schedule values exclude unrated opponents. Missing values are unavailable and never zero-filled. Conference comparisons and official polls remain in their existing views.</p></StatExplain></section>
}

export function IntelligenceMatchup({home,away}: {home:string;away:string}) {
  const {data}=useIntelligence(); const a=data?.teams.find(t=>t.team===home), b=data?.teams.find(t=>t.team===away)
  if (!a || !b || a.team===b.team) return null
  return <details className="profile-more"><summary>Matchup Intelligence · {home} vs {away}</summary><Takeaway>Compare each offense with the opposing defense. These descriptive rates are context, not an additional score prediction.</Takeaway><div className="table-wrap"><table><thead><tr><th>Evidence</th><th>{home}</th><th>{away}</th></tr></thead><tbody>{(['offense','defense'] as const).map(side=><tr key={side}><th>Adjusted {titleCase(side)} EPA/play</th><td>{metricNumber(a.units[side],3)}</td><td>{metricNumber(b.units[side],3)}</td></tr>)}<tr><th>Season Strength</th><td>{metricNumber(a.strength)}</td><td>{metricNumber(b.strength)}</td></tr><tr><th>Last-Three Level</th><td>{metricNumber(a.current_level)}</td><td>{metricNumber(b.current_level)}</td></tr><tr><th>Rated Schedule</th><td>{metricNumber(a.schedule)}</td><td>{metricNumber(b.schedule)}</td></tr></tbody></table></div><StatExplain label="Matchup Evidence & Limitations"><p>Higher offensive EPA and lower defensive EPA allowed are better. Do not subtract these rates to predict a margin: samples and opponent adjustment differ. Injuries, weather and personnel changes are not inferred. Official, Standard and Momentum projections retain their existing calculations.</p>{[a,b].map(t=><div key={t.team}><strong>{t.team}</strong><Evidence metric={t.units.offense}/><Evidence metric={t.units.defense}/></div>)}</StatExplain></details>
}
export function IntelligenceResearch() {
  const {data,status}=useIntelligence()
  return <section className="notice"><h2>Intelligence & Accountability</h2><Takeaway>{data ? `${data.teams.length} schools have published intelligence evidence. Existing forecasts remain unchanged.` : status}</Takeaway><StatExplain label="What Is Validated, and What Remains Conditional?"><p>Season strength and last-three playing level reuse released calculations. Four-game unit trends are descriptive with an explicit three-game fallback. Earned records are observed; no new accomplishment ranking is published. Retained snapshots are genuine observations and cannot fill missing historical weeks.</p><p>Pregame accountability and calibration must use authentic issued forecasts; retrospective calculations cannot enter those headlines. Existing research below keeps its cohort labels and limitations. Market Intelligence is a comparison tool within Research, not betting advice.</p><p>Source artifacts: season-report.json, v8-team-stats.json and team-intelligence.json. Source receipts and metric-level limitations are available within each team profile. The review build uses archived public data and makes no source API calls.</p></StatExplain></section>
}
export function PostseasonInterpretation() {
  return <StatExplain label="How to Interpret Postseason Implications"><p>CFP field probability estimates making the field, not winning the title. Conference-title probability and committee selection are different events. Existing simulations retain their simplified rules and published inputs.</p><p>Quantified personalized rooting advice is withheld until conference tiebreakers, interconnected outcomes and committee assumptions pass validation. Changing a scenario is conditional analysis, not a causal estimate of a single game's effect.</p></StatExplain>
}
