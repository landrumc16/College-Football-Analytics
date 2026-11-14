import { useEffect, useState } from 'react'

type Window = { seasons: number[]; games: number; fbs_win_rate: number | null; recruiting_seasons: number; rated_recruits: number; blue_chip_share: number | null }
type Program = { team: string; season: number; recent: Window; prior: Window; win_rate_change: number | null; blue_chip_share_change: number | null; recruiting: { players: number; star_rated: number; mean_stars: number | null; blue_chip_share: number | null } | null; roster: { players: number; retained_share_of_prior_roster: number | null; returning_observed_players: number | null } | null; coaching: { unambiguous_dominant_coach: boolean; consecutive_observed_seasons: number | null } | null; source_ids: string[] }
type Context = { schema_version: number; status: string; knowledge_as_of: string; programs: Program[]; coverage: { season: number; eligible_programs: number; all_domains: number }[]; sources: { id: string; url: string; sha256: string }[] }
const percentage = (x: number | null | undefined) => x == null ? 'Unavailable' : `${(100*x).toFixed(1)}%`
const change = (x: number | null) => x == null ? 'Unavailable' : `${x > 0 ? '+' : ''}${(100*x).toFixed(1)} pp`

export default function ProgramContext({ team }: { team: string }) {
  const [data,setData] = useState<Context | null>(null)
  const [failed,setFailed] = useState(false)
  useEffect(() => {
    let active=true
    fetch(import.meta.env.BASE_URL+'v6-program-context.json',{cache:'no-store'})
      .then(r=>{if(!r.ok || !r.headers.get('content-type')?.includes('json')) throw Error('Unavailable');return r.json()})
      .then((v: Context)=>{if(v.schema_version!==1 || v.status!=='descriptive_source_verified_not_historical_pregame' || !Array.isArray(v.programs)) throw Error('Unverified');if(active)setData(v)})
      .catch(()=>{if(active)setFailed(true)})
    return ()=>{active=false}
  },[])
  const p=data?.programs.find(p=>p.team===team)
  return <section className="accuracy-summary program-context" aria-label={`Program context for ${team}`}>
    <p className="section-kicker">THE PROGRAM FILE</p><h3>What’s changing at {team}</h3>
    {!p ? <p role="status">{failed || data ? 'Sourced program context is unavailable.' : 'Loading sourced program context…'}</p> : <>
      <p className="section-deck">Results, recruiting and continuity, side by side.</p>
      <div className="team-profile-grid">
        <div className="team-profile-tile"><small>FBS win-rate change</small><strong>{change(p.win_rate_change)}</strong></div>
        <div className="team-profile-tile"><small>Blue-chip recruiting change</small><strong>{change(p.blue_chip_share_change)}</strong></div>
        <div className="team-profile-tile"><small>{p.season} roster carryover</small><strong>{percentage(p.roster?.retained_share_of_prior_roster)}</strong></div>
        <div className="team-profile-tile"><small>Head-coach continuity</small><strong>{p.coaching?.unambiguous_dominant_coach && p.coaching.consecutive_observed_seasons ? `${p.coaching.consecutive_observed_seasons} seasons` : 'Unavailable / ambiguous'}</strong></div>
      </div>
      <p className="metric-note">Changes are percentage points (pp) between two three-season windows; 2020 is excluded. Blue-chip recruits have four or five stars. These records describe the program, not why it changed or how we predict games.</p>
      <details><summary>Periods, sources and limits</summary>
        <p>Source snapshot checked {new Date(data!.knowledge_as_of).toLocaleDateString()}.</p>
        <p>Recent completed seasons: {p.recent.seasons.join(', ') || 'Unavailable'} ({p.recent.games} FBS games, win rate {percentage(p.recent.fbs_win_rate)}). Prior: {p.prior.seasons.join(', ') || 'Unavailable'} ({p.prior.games} games, {percentage(p.prior.fbs_win_rate)}). 2020 excluded. Changes require two complete three-season windows.</p>
        <p>Recent recruiting: {p.recent.rated_recruits} rated recruits in {p.recent.recruiting_seasons} classes; prior: {p.prior.rated_recruits} in {p.prior.recruiting_seasons}. Blue-chip means four/five-star share among rated recruits; missing stars are excluded, never zero. These are signed recruiting classes, not proof of enrollment or development. {p.season} class: {p.recruiting?.players ?? 'unavailable'} recruits, {p.recruiting?.star_rated ?? 'unavailable'} rated.</p>
        <p>Roster retention is returning observed members divided by the prior observed roster, not returning snaps, playing eligibility or transfer-only retention. Coach continuity uses unambiguous dominant-season attribution, not exact hire dates, coordinators or current staff. These associations cannot establish why results changed. V5 trajectories and Report Card grades remain separate.</p>
        <p>National coverage: {data!.coverage.map(c=>`${c.season}: ${c.all_domains}/${c.eligible_programs} all domains`).join(' · ')}. Historical original publication times are unverified; these snapshots are excluded from historical challenger fitting.</p>
        <p>SportsDataverse/cfbfastR-cfb-data, Saiem Gilani (CC BY 4.0); upstream ESPN rosters, 247Sports recruiting and CFBD coach seasons. Only derived aggregates are redistributed.</p>
        <ul>{data!.sources.filter(s=>p.source_ids.includes(s.id)).map(s=><li key={s.id}><a href={s.url} target="_blank" rel="noreferrer">{s.id}</a> <small>SHA-256 {s.sha256}</small></li>)}</ul>
      </details>
    </>}
  </section>
}
