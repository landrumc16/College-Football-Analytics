import { useEffect, useState } from 'react'
type Metrics = { brier_score: number; log_loss: number; winner_accuracy: number }
type Score = { games: number; reference: Metrics; challenger: Metrics; relative_brier_reduction: number }
type Research = { model_status: string; promotion: { eligible: boolean; incumbent_retained: boolean; blockers: string[] }; chronological_research: { retrospective: Score; retrospective_by_season: Record<string,Score>; by_home_conference: Record<string,Score>; reference_screen: { criteria: Record<string,boolean>; challenger_ece: number; reference_ece: number }; clustered_challenger_minus_reference_interval: { ci95_lower: number; ci95_upper: number; clusters: number; draws: number } }; folds: { season: number; paired_games: number; eligible_games: number; feature_coverage: number; missing_history_games: number }[] }
export default function PredictionResearch() {
  const [data,setData]=useState<Research|null>(null)
  const [failed,setFailed]=useState(false)
  useEffect(()=>{let active=true;fetch(import.meta.env.BASE_URL+'v6-prediction-research.json',{cache:'no-store'})
    .then(r=>{if(!r.ok || !r.headers.get('content-type')?.includes('json'))throw Error();return r.json()})
    .then((v:Research)=>{if(v.model_status!=='experimental_not_promoted' || !v.promotion.incumbent_retained || !v.chronological_research.retrospective)throw Error();if(active)setData(v)})
    .catch(()=>{if(active)setFailed(true)});return()=>{active=false}},[])
  if(!data)return <section className="accuracy-summary" aria-label="Experimental prediction research"><h3>Experimental prediction research</h3><p role="status">{failed?'Research evidence unavailable. The incumbent remains authoritative.':'Loading frozen research evidence…'}</p></section>
  const r=data.chronological_research,p=r.retrospective,ci=r.clustered_challenger_minus_reference_interval
  const table=(items:Record<string,Score>)=><div className="table-wrap"><table><thead><tr><th>Research cohort</th><th>Games</th><th>Reference Brier</th><th>Challenger Brier</th><th>Challenger accuracy</th><th>Log loss</th></tr></thead><tbody>{Object.entries(items).map(([name,v])=><tr key={name}><th scope="row">{name}</th><td>{v.games}</td><td>{v.reference.brier_score.toFixed(4)}</td><td>{v.challenger.brier_score.toFixed(4)}</td><td>{(100*v.challenger.winner_accuracy).toFixed(1)}%</td><td>{v.challenger.log_loss.toFixed(4)}</td></tr>)}</tbody></table></div>
  return <section className="accuracy-summary" aria-label="Experimental prediction research"><h3>Challenger research · incumbent retained</h3>
    <p>No production accuracy improvement is established. This is a chronological replay of {p.games.toLocaleString()} games in four held-out seasons, compared with a prior-results reference proxy. The proxy is not the production incumbent; these are not archived live challenger forecasts.</p>
    {table({'2022–2025 pooled':p,...r.retrospective_by_season})}
    <p>Paired challenger-minus-reference Brier 95% interval: {ci.ci95_lower.toFixed(5)} to {ci.ci95_upper.toFixed(5)} ({ci.draws.toLocaleString()} bootstrap draws, {ci.clusters} season/week clusters). An interval crossing zero does not establish improvement. Lower Brier and log loss are better.</p>
    <details><summary>Coverage, calibration, gates and conference breakdown</summary>
      <p>Only lagged completed non-2020 FBS results and game location enter this experiment. Recruiting, roster and coaching snapshots are excluded because original historical cutoff availability is unverified. Training expands before each held-out season with no held-out tuning.</p>
      <p>{data.folds.map(f=>`${f.season}: ${f.paired_games}/${f.eligible_games} games (${(100*f.feature_coverage).toFixed(1)}%); ${f.missing_history_games} abstentions for insufficient history`).join(' · ')}.</p>
      <p>Ten-bin weighted calibration error: reference {r.reference_screen.reference_ece.toFixed(4)}, challenger {r.reference_screen.challenger_ece.toFixed(4)}. Missing history is never zero-imputed.</p>
      <ul>{Object.entries(r.reference_screen.criteria).map(([k,v])=><li key={k}>{k.replaceAll('_',' ')}: {v?'met':'not met'} (proxy screen only)</li>)}</ul>
      {table(r.by_home_conference)}
      <p>Conference groups use the home team's historical season attribution; cross-conference games remain in the home group. Small subgroups are descriptive, not proof of a stable edge.</p>
      <ul>{data.promotion.blockers.map(b=><li key={b}>{b}</li>)}</ul>
      <p><a href={`${import.meta.env.BASE_URL}v6-prediction-research.json`}>Frozen protocol, calibration bins, inputs and full research evidence</a>. The authentic 65-game incumbent archive above is reported separately.</p>
    </details>
  </section>
}
