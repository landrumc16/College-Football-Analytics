/** Browser implementation of cfp.py's incumbent simulation rules, isolated from forecasts. */
export type ScenarioTeam = { conference: string; rating: number; wins: number; conference_wins: number }
export type ScenarioGame = { game_id: number; week: number; home: string; away: string; completed: boolean; neutral_site: boolean; start_date: string | null }
export type ScenarioInput = { schema_version: number; season: number; retrieved_at: string | null; report_sha256: string; teams: Record<string,ScenarioTeam>; games: ScenarioGame[]; scale: number; home_edge: number; fcs_rating: number; draws: number; seed: number }
export type ScenarioResult = { teams: { team: string; conference_title: number; cfp_field: number; national_title: number }[]; milliseconds: number }
const cmp=(a:string,b:string)=>a<b?-1:a>b?1:0
const round=(n:number)=>Math.round(n*10000)/10000
export function simulate(data:ScenarioInput, overrides:Record<string,string>, now:string):ScenarioResult {
  const start=performance.now(),time=Date.parse(now),names=Object.keys(data.teams).sort(cmp),teams=data.teams
  if(!Number.isFinite(time) || names.length<12 || data.draws!==2000 || data.scale<=0)throw Error('Invalid scenario inputs')
  const byId=new Map(data.games.map(g=>[String(g.game_id),g]))
  if(byId.size!==data.games.length)throw Error('Duplicate game identity')
  for(const [id,winner] of Object.entries(overrides)) {
    const g=byId.get(id)
    if(!g || g.completed || ![g.home,g.away].includes(winner) || !g.start_date || !Number.isFinite(Date.parse(g.start_date)) || Date.parse(g.start_date)<=time)throw Error('Only valid future-game winners can be selected')
  }
  for(const t of Object.values(teams))if(!Number.isFinite(t.rating) || !Number.isInteger(t.wins) || t.wins<0 || !Number.isInteger(t.conference_wins) || t.conference_wins<0 || !t.conference)throw Error('Invalid team observation')
  let state=data.seed>>>0
  const random=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296}
  const p=(gap:number)=>1/(1+Math.pow(10,-gap/data.scale))
  const conferences:Record<string,string[]>={}
  for(const n of names)if(teams[n].conference!=='Independent')(conferences[teams[n].conference]??=[]).push(n)
  const ratingMean=names.reduce((s,n)=>s+teams[n].rating,0)/names.length
  const ratingStd=Math.sqrt(names.reduce((s,n)=>s+(teams[n].rating-ratingMean)**2,0)/names.length)||1
  const ratingZ=Object.fromEntries(names.map(n=>[n,(teams[n].rating-ratingMean)/ratingStd]))
  const seen=new Set<string>()
  const prepared=data.games.filter(g=>teams[g.home]||teams[g.away]).map(g=>{
    const key=[g.home,g.away].sort(cmp).join('|')
    if(seen.has(key)||g.home===g.away||g.completed)throw Error('Invalid remaining schedule')
    seen.add(key)
    return { ...g,probability:p((teams[g.home]?.rating??data.fcs_rating)-(teams[g.away]?.rating??data.fcs_rating)+(g.neutral_site?0:data.home_edge)),same:teams[g.home]&&teams[g.away]&&teams[g.home].conference===teams[g.away].conference&&teams[g.home].conference!=='Independent' }
  })
  const totals=Object.fromEntries(names.map(n=>[n,{team:n,conference_title:0,cfp_field:0,national_title:0}]))
  for(let draw=0;draw<data.draws;draw++) {
    const wins=Object.fromEntries(names.map(n=>[n,teams[n].wins])),confWins=Object.fromEntries(names.map(n=>[n,teams[n].conference_wins]))
    for(const g of prepared) {
      const drawn=random()<g.probability?g.home:g.away,winner=overrides[String(g.game_id)]||drawn
      if(winner in wins){wins[winner]++;if(g.same)confWins[winner]++}
    }
    const champions:string[]=[]
    for(const members of Object.values(conferences)) {
      const finalists=[...members].sort((a,b)=>confWins[b]-confWins[a]||teams[b].rating-teams[a].rating||cmp(a,b)).slice(0,2)
      const champion=finalists.length===1?finalists[0]:random()<p(teams[finalists[0]].rating-teams[finalists[1]].rating)?finalists[0]:finalists[1]
      champions.push(champion);totals[champion].conference_title++;if(finalists.length===2)wins[champion]++
    }
    const mean=names.reduce((s,n)=>s+wins[n],0)/names.length,std=Math.sqrt(names.reduce((s,n)=>s+(wins[n]-mean)**2,0)/names.length)||1
    const scores=Object.fromEntries(names.map(n=>[n,.5*(wins[n]-mean)/std+.5*ratingZ[n]]))
    const order=(a:string,b:string)=>scores[b]-scores[a]||cmp(a,b)
    const auto=champions.sort(order).slice(0,5),others=names.filter(n=>!auto.includes(n)).sort(order)
    const field=[...auto,...others.slice(0,7)].sort(order)
    for(const n of field)totals[n].cfp_field++
    if(field.length!==12)continue
    const game=(a:string,b:string)=>random()<p(teams[a].rating-teams[b].rating)?a:b
    const first=[[5,12],[6,11],[7,10],[8,9]].map(([a,b])=>game(field[a-1],field[b-1]))
    const quarter=[4,3,2,1].map((seed,i)=>game(field[seed-1],first[i]))
    const semis=[game(quarter[0],quarter[3]),game(quarter[1],quarter[2])]
    totals[game(semis[0],semis[1])].national_title++
  }
  return {teams:names.map(n=>({team:n,conference_title:round(totals[n].conference_title/data.draws),cfp_field:round(totals[n].cfp_field/data.draws),national_title:round(totals[n].national_title/data.draws)})),milliseconds:performance.now()-start}
}
