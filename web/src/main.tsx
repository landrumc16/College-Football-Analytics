import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type Team = { rank: number; team: string; rating: number; wins: number; losses: number; projected_wins: number; projected_conference_wins: number; rank_score: number }
type Prediction = { game_id: number; week: number; home: string; away: string; predicted_winner: string; home_margin: number; home_win_probability: number; confidence: string }
type CfpTeam = { team: string; conference: string; most_likely_seed: number | null; average_seed_when_selected: number | null; average_wins: number; wins_p10: number; wins_p90: number; bowl_eligible: number; cfp_field: number; first_round_bye: number; quarterfinal: number; semifinal: number; final: number; national_title: number }
type ConferenceTeam = { team: string; conference_wins: number; conference_losses: number; wins: number; losses: number; rating: number; projected_conference_wins: number; conference_title_odds: number; cfp_odds: number }
type Bracket = { methodology: string; conference_championships?: { conference: string; first: string; second: string; projected_champion: string }[]; seeds: { seed: number; team: string; conference: string; bid: string; bye: boolean }[]; first_round: { home_seed: number; away_seed: number; home: string; away: string }[] }
type Report = { projected_bracket?: Bracket; cfp?: { simulations: number; methodology: string; teams: CfpTeam[] }; conference_standings?: Record<string, ConferenceTeam[]>; conference_strength?: { conference: string; teams: number; average_rating: number; best_team: string }[]; season: number; source?: string; retrieved_at?: string | null; data_changed_at?: string | null; summary: { teams: number; completed_games: number; upcoming_games: number }; rankings: Team[]; predictions: Prediction[] }

const pct = (p: number) => (p * 100).toFixed(1) + '%'
const num = (n: number) => n.toFixed(2)
// Same rating-gap logistic function and home advantage as the Python prediction model.
const hypothetical = (home: Team, away: Team, neutral: boolean) => {
  const margin = home.rating - away.rating + (neutral ? 0 : 3)
  const homeProbability = 1 / (1 + Math.pow(10, -margin / 18))
  const certainty = Math.max(homeProbability, 1 - homeProbability)
  const confidence = certainty > .8 ? 'Strong' : certainty > .65 ? 'Likely' : certainty > .55 ? 'Lean' : 'Toss-up'
  return { margin, homeProbability, winner: homeProbability >= .5 ? home.team : away.team, confidence }
}

function App() {
  const [report, setReport] = useState<Report | null>(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'rankings' | 'predictions' | 'conferences' | 'cfp' | 'matchup'>('rankings')
  const [search, setSearch] = useState('')
  const [week, setWeek] = useState('all')
  const [conference, setConference] = useState('Big 12')
  const [homeTeam, setHomeTeam] = useState('')
  const [awayTeam, setAwayTeam] = useState('')
  const [venue, setVenue] = useState<'home' | 'away' | 'neutral'>('home')

  useEffect(() => {
    fetch(import.meta.env.BASE_URL + 'season-report.json', { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error('No published season report is available yet.'); return r.json() })
      .then((data: Report) => {
        if (!Array.isArray(data.rankings) || !Array.isArray(data.predictions)) throw new Error('Invalid report format')
        setReport(data)
      })
      .catch(e => setError(String(e.message || e)))
  }, [])

  const weeks = useMemo(() => [...new Set(report?.predictions.map(p => p.week) || [])].sort((a, b) => a - b), [report])
  const teams = useMemo(() => (report?.rankings || []).filter(t => t.team.toLowerCase().includes(search.toLowerCase())), [report, search])
  const predictions = useMemo(() => (report?.predictions || []).filter(p =>
    (week === 'all' || p.week === Number(week)) &&
    [p.home, p.away, p.predicted_winner].some(s => s.toLowerCase().includes(search.toLowerCase()))
  ), [report, week, search])

  const isDemo = !!report?.source?.includes('DEMO')
  const retrievedTime = report?.retrieved_at ? Date.parse(report.retrieved_at) : NaN
  const freshnessUnknown = !!report && !isDemo && !Number.isFinite(retrievedTime)
  const staleData = !!report && !isDemo && Number.isFinite(retrievedTime) &&
    (retrievedTime > Date.now() + 60 * 60 * 1000 || Date.now() - retrievedTime > 72 * 60 * 60 * 1000)

  const conferences = Object.keys(report?.conference_standings || {}).sort()
  const selectedConference = conferences.includes(conference) ? conference : (conferences[0] || '')
  const conferenceRows = (report?.conference_standings?.[selectedConference] || []).filter(t => t.team.toLowerCase().includes(search.toLowerCase()))
  const bracketByTeam = new Map((report?.projected_bracket?.seeds || []).map(s => [s.team, s]))
  const cfpRows = (report?.cfp?.teams || []).filter(t => t.team.toLowerCase().includes(search.toLowerCase()))
  const sortedTeams = [...(report?.rankings || [])].sort((a, b) => a.team.localeCompare(b.team))
  const selectedHome = report?.rankings.find(t => t.team === homeTeam)
  const selectedAway = report?.rankings.find(t => t.team === awayTeam)
  const actualHome = venue === 'away' ? selectedAway : selectedHome
  const actualAway = venue === 'away' ? selectedHome : selectedAway
  const matchup = actualHome && actualAway && homeTeam !== awayTeam ? hypothetical(actualHome, actualAway, venue === 'neutral') : null
  return <main className="app">
    <header><div className="eyebrow">SEASON INTELLIGENCE</div><h1>College Football <span>Analytics</span></h1><p>Model-driven rankings, season outlooks and upcoming game forecasts.</p></header>
    {error ? <section className="notice"><strong>Waiting for live data</strong><p>{error}</p><p>Run the repository's refresh workflow to publish a season report.</p></section> : null}
    {report && <>
      {report.source?.includes("DEMO") && <section className="notice"><strong>Historical demonstration — not live rankings</strong><p>This view uses the frozen 2026 Week 7 workbook baseline. Live rankings will replace it after the CFBD refresh is verified.</p></section>}
      {(freshnessUnknown || staleData) && <section className="notice"><strong>Data freshness warning</strong><p>{freshnessUnknown ? 'This report has no valid retrieval timestamp; live-data freshness cannot be verified.' : 'This report was retrieved more than 72 hours ago (or has a future timestamp). Rankings and forecasts may be outdated.'}</p></section>}
      <div className="stats"><article><small>SEASON</small><strong>{report.season}</strong></article><article><small>TEAMS RANKED</small><strong>{report.summary.teams}</strong></article><article><small>COMPLETED GAMES</small><strong>{report.summary.completed_games}</strong></article><article><small>UPCOMING GAMES</small><strong>{report.summary.upcoming_games}</strong></article></div>
      <div className="toolbar"><div className="tabs"><button className={tab === 'rankings' ? 'active' : ''} onClick={() => setTab('rankings')}>Rankings</button><button className={tab === 'predictions' ? 'active' : ''} onClick={() => setTab('predictions')}>Game predictions</button><button className={tab === 'conferences' ? 'active' : ''} onClick={() => setTab('conferences')}>Conferences</button><button className={tab === 'cfp' ? 'active' : ''} onClick={() => setTab('cfp')}>CFP forecast</button><button className={tab === 'matchup' ? 'active' : ''} onClick={() => setTab('matchup')}>What if?</button></div><input aria-label="Search teams" placeholder="Search teams…" value={search} onChange={e => setSearch(e.target.value)}/>{tab === 'conferences' && <select aria-label="Select conference" value={selectedConference} onChange={e => setConference(e.target.value)}>{conferences.map(name => <option key={name} value={name}>{name}</option>)}</select>}{tab === 'predictions' && <select aria-label="Filter by week" value={week} onChange={e => setWeek(e.target.value)}><option value="all">All weeks</option>{weeks.map(w => <option key={w} value={w}>Week {w}</option>)}</select>}</div>
      {tab === 'matchup' && <section className="matchup-panel"><h2>Hypothetical matchup</h2><p>Choose two schools and a game location to see the model's predicted winner, margin, and win probability.</p><div className="matchup-inputs"><label>School 1<select aria-label="First school" value={homeTeam} onChange={e => setHomeTeam(e.target.value)}><option value="">Select school</option>{sortedTeams.map(t => <option key={t.team} value={t.team}>{t.team}</option>)}</select></label><label>School 2<select aria-label="Second school" value={awayTeam} onChange={e => setAwayTeam(e.target.value)}><option value="">Select school</option>{sortedTeams.map(t => <option key={t.team} value={t.team}>{t.team}</option>)}</select></label><label>Game location<select aria-label="Game location" value={venue} onChange={e => setVenue(e.target.value as 'home' | 'away' | 'neutral')}><option value="home">At School 1</option><option value="away">At School 2</option><option value="neutral">Neutral site</option></select></label></div><div className="matchup-actions"><button type="button" onClick={() => { setHomeTeam(awayTeam); setAwayTeam(homeTeam) }}>Swap schools</button><button type="button" onClick={() => { setHomeTeam(""); setAwayTeam(""); setVenue("home") }}>Reset matchup</button></div>{homeTeam && homeTeam === awayTeam && <p role="alert">Choose two different schools.</p>}{matchup && <div className="matchup-result" aria-live="polite"><small>MODEL PROJECTED WINNER</small><h3>{matchup.winner}</h3><strong>{matchup.confidence} · {num(Math.abs(matchup.margin))}-point projected margin</strong><div className="matchup-odds"><div><span>{actualHome!.team}</span><strong>{pct(matchup.homeProbability)}</strong></div><div><span>{actualAway!.team}</span><strong>{pct(1 - matchup.homeProbability)}</strong></div></div><p>{venue === 'neutral' ? 'Neutral site: no home-field advantage' : `Home: ${actualHome!.team} (+3-point home-field advantage)`} · Ratings from the current published season report. Probabilities are estimates, not guarantees.</p></div>}</section>}
      {tab === 'cfp' && <p className="table-legend"><span className="auto-bid" aria-hidden="true">A</span> Projected automatic bid · # is the most likely seed when selected (not an official seed).</p>}
      {tab !== 'matchup' && <div className="table-wrap">{tab === 'rankings' ? <table><thead><tr><th>Team / rank</th><th>Record</th><th>Rating</th><th>Projected wins</th><th>Conf. wins</th></tr></thead><tbody>{teams.map(t => <tr key={t.team}><td className="team"><span className="team-number">#{t.rank}</span>{t.team}</td><td>{t.wins}–{t.losses}</td><td>{num(t.rating)}</td><td className="emphasis">{num(t.projected_wins)}</td><td>{num(t.projected_conference_wins)}</td></tr>)}</tbody></table> : tab === 'predictions' ? <table><thead><tr><th>Matchup</th><th>Week</th><th>Projected winner</th><th>Home win %</th><th>Margin (home)</th><th>Confidence</th></tr></thead><tbody>{predictions.map(p => <tr key={p.game_id}><td className="team">{p.away} <span className="muted">@</span> {p.home}</td><td>{p.week}</td><td className="emphasis">{p.predicted_winner}</td><td>{pct(p.home_win_probability)}</td><td>{p.home_margin > 0 ? '+' : ''}{num(p.home_margin)}</td><td>{p.confidence}</td></tr>)}</tbody></table> : tab === 'conferences' ? <table><thead><tr><th>Team</th><th>Conf. record</th><th>Overall</th><th>Rating</th><th>Projected conf. wins</th><th>Title odds</th><th>CFP odds</th></tr></thead><tbody>{conferenceRows.map(t => <tr key={t.team}><td className="team">{t.team}</td><td>{t.conference_wins}–{t.conference_losses}</td><td>{t.wins}–{t.losses}</td><td>{num(t.rating)}</td><td>{num(t.projected_conference_wins)}</td><td>{pct(t.conference_title_odds)}</td><td>{pct(t.cfp_odds)}</td></tr>)}</tbody></table> : <table><thead><tr><th>Team / likely seed</th><th>Conference</th><th>Avg wins</th><th>80% wins range</th><th>Bowl eligible</th><th>CFP field</th><th>Avg seed</th><th>Bye</th><th>Quarterfinal</th><th>Semifinal</th><th>Final</th><th>National title</th></tr></thead><tbody>{cfpRows.map(t => <tr key={t.team}><td className="team">{t.most_likely_seed != null && <span className="team-number">#{t.most_likely_seed}</span>}{t.team}{bracketByTeam.get(t.team)?.bid === "automatic" && <span className="auto-bid" title="Projected automatic CFP qualifier" aria-label="Projected automatic CFP qualifier">A</span>}</td><td>{t.conference}</td><td>{num(t.average_wins)}</td><td>{t.wins_p10}–{t.wins_p90}</td><td>{pct(t.bowl_eligible)}</td><td>{pct(t.cfp_field)}</td><td>{t.average_seed_when_selected == null ? "—" : num(t.average_seed_when_selected)}</td><td>{pct(t.first_round_bye)}</td><td>{pct(t.quarterfinal)}</td><td>{pct(t.semifinal)}</td><td>{pct(t.final)}</td><td className="emphasis">{pct(t.national_title)}</td></tr>)}</tbody></table>}</div>}
      {tab === 'cfp' && report.projected_bracket && <section className="notice"><h2>Projected 12-team bracket</h2><p>{report.projected_bracket.methodology}</p><p><span className="auto-bid">A</span> Projected automatic qualifier · Other teams receive at-large bids. These are model projections, not official CFP selections.</p><div className="table-wrap"><table><thead><tr><th>Seed / team</th><th>Conference</th><th>Bid</th><th>First round</th></tr></thead><tbody>{report.projected_bracket.seeds.map(s => <tr key={s.seed}><td className="team"><span className="team-number">#{s.seed}</span>{s.team}{s.bid === "automatic" && <span className="auto-bid" title="Projected automatic CFP qualifier">A</span>}</td><td>{s.conference}</td><td>{s.bid === 'automatic' ? 'Automatic' : 'At-large'}</td><td>{s.bye ? 'Bye' : 'Plays'}</td></tr>)}</tbody></table></div><h3>Opening-round matchups</h3><div className="table-wrap"><table><thead><tr><th>Higher seed</th><th>Lower seed</th></tr></thead><tbody>{report.projected_bracket.first_round.map(m => <tr key={m.home_seed}><td className="team"><span className="team-number">#{m.home_seed}</span>{m.home}</td><td className="team"><span className="team-number">#{m.away_seed}</span>{m.away}</td></tr>)}</tbody></table></div></section>}
      {tab === 'conferences' && !!report.projected_bracket?.conference_championships?.length && <><h2>Projected conference championship games</h2><div className="table-wrap"><table><thead><tr><th>Conference</th><th>Projected finalists</th><th>Model favorite</th></tr></thead><tbody>{report.projected_bracket.conference_championships.filter(m => selectedConference === m.conference).map(m => <tr key={m.conference}><td className="team">{m.conference}</td><td>{m.first} vs {m.second}</td><td className="emphasis">{m.projected_champion}</td></tr>)}</tbody></table></div></>}
      {tab === 'cfp' && <section className="notice"><strong>{report.cfp?.simulations?.toLocaleString() || 'No'} CFP simulations</strong><p>{report.cfp?.methodology || 'Rebuild the season report to enable CFP forecasting.'}</p></section>}
      {tab === 'conferences' && !!report.conference_strength?.length && <><h2>Conference strength</h2><div className="table-wrap"><table><thead><tr><th>Conference</th><th>Teams</th><th>Average rating</th><th>Best team</th></tr></thead><tbody>{report.conference_strength.map(c => <tr key={c.conference}><td className="team">{c.conference}</td><td>{c.teams}</td><td>{num(c.average_rating)}</td><td>{c.best_team}</td></tr>)}</tbody></table></div></>}
      <footer>Model estimates are probabilistic, not guarantees. Data source: {report.source || 'CFBD'}. {report.retrieved_at ? `Last successful data check: ${new Date(report.retrieved_at).toLocaleString()}.` : 'Historical fixture or retrieval date unavailable.'} {report.data_changed_at ? `Game data last changed: ${new Date(report.data_changed_at).toLocaleString()}.` : ''}</footer>
    </>}
  </main>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
