import { useEffect, useRef, useState } from 'react'
import type { ScenarioInput, ScenarioResult } from './scenarios'
const pct=(n:number)=>`${(100*n).toFixed(1)}%`
export default function PlayoffScenarios({ retrievedAt, favorites, published }: { retrievedAt?: string | null; favorites: (string|null)[]; published: {team:string;cfp_field:number}[] }) {
  const [input,setInput]=useState<ScenarioInput|null>(null),[error,setError]=useState(''),[open,setOpen]=useState(false)
  const [overrides,setOverrides]=useState<Record<string,string>>({}),[result,setResult]=useState<ScenarioResult|null>(null),[baseline,setBaseline]=useState<ScenarioResult|null>(null)
  const [gameId,setGameId]=useState(''),[busy,setBusy]=useState(false),[showAll,setShowAll]=useState(false)
  const worker=useRef<Worker|null>(null)
  useEffect(()=>{
    let active=true
    setInput(null);setError('');setBaseline(null);setResult(null);setOverrides({})
    Promise.all([fetch(import.meta.env.BASE_URL+'v6-scenario-input.json',{cache:'no-store'}).then(r=>{if(!r.ok || !r.headers.get('content-type')?.includes('json'))throw Error('Scenario data unavailable');return r.json()}),fetch(import.meta.env.BASE_URL+'season-report.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Report unavailable');return r.arrayBuffer()})])
      .then(async([data,bytes]:[ScenarioInput,ArrayBuffer])=>{
        const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(n=>n.toString(16).padStart(2,'0')).join('')
        if(hash!==data.report_sha256 || data.retrieved_at!==retrievedAt || data.schema_version!==1)throw Error('Scenario snapshot differs from the current report. Refresh to retry.')
        if(!Number.isFinite(data.scale) || data.scale<=0 || !Number.isFinite(data.home_edge) ||
           !Number.isFinite(data.fcs_rating) || !Number.isInteger(data.seed) || data.seed<0 || data.seed>0xffffffff ||
           data.draws!==2000 || !data.teams || typeof data.teams!=='object' || Array.isArray(data.teams) ||
           !Array.isArray(data.games))throw Error('Scenario data is invalid. Published forecasts remain unchanged. Refresh to retry.')
        if(active)setInput(data)
      }).catch(e=>{if(active)setError(String(e.message||e))})
    return()=>{active=false;worker.current?.terminate()}
  },[retrievedAt])
  useEffect(()=>{
    if(!input || !open)return
    worker.current?.terminate();setBusy(true);setError('')
    const w=new Worker(new URL('./scenario.worker.ts',import.meta.url),{type:'module'});worker.current=w
    w.onmessage=event=>{
      if(event.data.error)setError(event.data.error)
      else {setResult(event.data.result);if(!Object.keys(overrides).length)setBaseline(event.data.result)}
      setBusy(false);w.terminate()
    }
    w.onerror=()=>{setError('Scenario computation unavailable. Published forecasts remain unchanged.');setBusy(false);w.terminate()}
    w.postMessage({input,overrides,now:new Date().toISOString()})
    return()=>w.terminate()
  },[input,overrides,open])
  const future=input?.games.filter(g=>!g.completed && g.start_date && Date.parse(g.start_date)>Date.now())||[]
  const selected=future.find(g=>String(g.game_id)===gameId)
  const rows=[...(result?.teams||[])].sort((a,b)=>Number(favorites.includes(b.team))-Number(favorites.includes(a.team))||b.cfp_field-a.cfp_field||a.team.localeCompare(b.team))
  return <section className="notice playoff-scenarios" aria-label="Playoff what-if scenarios"><p className="section-kicker">CHANGE THE RESULT</p><h2>Playoff what-if</h2>
    <p>Pick a winner. See how the conference and CFP picture shifts. Your choices leave our published forecasts unchanged.</p>
    {!open && <button type="button" onClick={()=>setOpen(true)}>Explore scenarios</button>}
    {error && <p role="alert">{error}</p>}
    {open && !input && !error && <p role="status">Checking scenario snapshot…</p>}
    {open && input && <>
      <div className="scenario-controls"><label>Matchup<select aria-label="Scenario matchup" disabled={busy || !baseline} value={gameId} onChange={e=>setGameId(e.target.value)}><option value="">Choose a game</option>{future.map(g=><option key={g.game_id} value={g.game_id}>W{g.week}: {g.away} at {g.home}</option>)}</select></label>
      {selected && <label>Your winner<select aria-label="Scenario winner" disabled={busy || !baseline} value={overrides[gameId]||''} onChange={e=>setOverrides(old=>{const next={...old};if(e.target.value)next[gameId]=e.target.value;else delete next[gameId];return next})}><option value="">Model probabilities</option><option value={selected.home}>{selected.home}</option><option value={selected.away}>{selected.away}</option></select></label>}
      <button type="button" onClick={()=>{setOverrides({});setGameId('')}}>Reset to baseline</button></div>
      <p role="status" aria-live="polite">{busy?'Updating the odds…':result?Object.keys(overrides).length ? `${Object.keys(overrides).length} pick${Object.keys(overrides).length===1?'':'s'} applied` : 'No picks selected · model baseline':'Choose a future matchup.'}</p>
      {Object.keys(overrides).length>0 && <ul className="scenario-picks">{Object.entries(overrides).map(([id,winner])=>{const g=input.games.find(g=>String(g.game_id)===id);return <li key={id}>{g?.away} at {g?.home}: {winner} wins <button type="button" aria-label={`Remove ${winner} scenario choice`} onClick={()=>setOverrides(old=>{const next={...old};delete next[id];return next})}>Remove</button></li>})}</ul>}
      {result && baseline && <div className="table-wrap" aria-busy={busy}><table><caption>Chance to make the CFP</caption><thead><tr><th>Team</th><th>No picks</th><th>With your picks</th><th>Change</th><th>Conference title</th></tr></thead><tbody>{(showAll?rows:rows.slice(0,12)).map(t=>{const b=baseline.teams.find(b=>b.team===t.team)!.cfp_field,delta=t.cfp_field-b;return <tr key={t.team}><th scope="row">{t.team}</th><td>{pct(b)}</td><td>{pct(t.cfp_field)}</td><td>{delta>0?'+':''}{(delta*100).toFixed(1)} pp</td><td>{pct(t.conference_title)}</td></tr>})}</tbody></table></div>}
      {result && <button type="button" onClick={()=>setShowAll(v=>!v)}>{showAll?'Show leading teams':'Show all scenario teams'}</button>}
      <p className="metric-note">A model scenario, not a committee decision. The baseline uses 2,000 simulated seasons; it can differ slightly from the published 10,000-season forecast.</p><details><summary>How these scenarios work</summary><p>Last run: {result?.milliseconds.toFixed(0) ?? "—"} ms. Computation timing is diagnostic, not a measure of forecast quality.</p><p>Same ratings, location adjustment and selection rules as the incumbent Python simulator. Top two conference-win teams play a neutral-site title game; ties use rating then name. Five highest-ranked champions plus seven at-large teams; win/rating scores seed the field. Real conference tiebreakers and committee judgment are not modeled. Same-conference status is inferred from membership; special nonconference games between conference members are not separately modeled. These are conditional model estimates, not official CFP decisions.</p><p>Seed {input.seed}; 2,000 draws per run. Worst-case single-probability 95% Monte Carlo half-width is about 2.2 percentage points; a difference between independent runs is about 3.1 points. Common random draws reduce comparison noise. This lower-draw baseline is separate from the published 10,000-draw forecast. Reset reproduces this baseline exactly. Results use the checked report from {input.retrieved_at||'an unspecified date'}; a stale snapshot does not become live data.</p><p>Only scheduled future games can be selected. Changing a winner does not change ratings or invent a score. Completed games are fixed; unknown kickoff times and already-started games cannot be overridden. Favorites appear first.</p><p>Published CFP values remain available in the full table below ({published.length} teams).</p></details>
    </>}
  </section>
}
