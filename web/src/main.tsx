import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

type Team = { rank: number; team: string; rating: number; wins: number; losses: number; projected_wins: number; projected_conference_wins: number; rank_score: number }
type Prediction = { game_id: number; week: number; home: string; away: string; predicted_winner: string; home_margin: number; home_win_probability: number; confidence: string }
type Report = { season: number; source?: string; summary: { teams: number; completed_games: number; upcoming_games: number }; rankings: Team[]; predictions: Prediction[] }

const pct = (p: number) => (p * 100).toFixed(1) + '%'
const num = (n: number) => n.toFixed(2)

function App() {
  const [report, setReport] = useState<Report | null>(null)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'rankings' | 'predictions'>('rankings')
  const [search, setSearch] = useState('')
  const [week, setWeek] = useState('all')

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

  return <main className="app">
    <header><div className="eyebrow">SEASON INTELLIGENCE</div><h1>College Football <span>Analytics</span></h1><p>Model-driven rankings, season outlooks and upcoming game forecasts.</p></header>
    {error ? <section className="notice"><strong>Waiting for live data</strong><p>{error}</p><p>Run the repository's refresh workflow to publish a season report.</p></section> : null}
    {report && <>
      <div className="stats"><article><small>SEASON</small><strong>{report.season}</strong></article><article><small>TEAMS RANKED</small><strong>{report.summary.teams}</strong></article><article><small>COMPLETED GAMES</small><strong>{report.summary.completed_games}</strong></article><article><small>UPCOMING GAMES</small><strong>{report.summary.upcoming_games}</strong></article></div>
      <div className="toolbar"><div className="tabs"><button className={tab === 'rankings' ? 'active' : ''} onClick={() => setTab('rankings')}>Rankings</button><button className={tab === 'predictions' ? 'active' : ''} onClick={() => setTab('predictions')}>Game predictions</button></div><input aria-label="Search teams" placeholder="Search teams…" value={search} onChange={e => setSearch(e.target.value)}/>{tab === 'predictions' && <select aria-label="Filter by week" value={week} onChange={e => setWeek(e.target.value)}><option value="all">All weeks</option>{weeks.map(w => <option key={w} value={w}>Week {w}</option>)}</select>}</div>
      <div className="table-wrap">{tab === 'rankings' ? <table><thead><tr><th>Rank</th><th>Team</th><th>Record</th><th>Rating</th><th>Projected wins</th><th>Conf. wins</th></tr></thead><tbody>{teams.map(t => <tr key={t.team}><td className="rank">{t.rank}</td><td className="team">{t.team}</td><td>{t.wins}–{t.losses}</td><td>{num(t.rating)}</td><td className="emphasis">{num(t.projected_wins)}</td><td>{num(t.projected_conference_wins)}</td></tr>)}</tbody></table> : <table><thead><tr><th>Week</th><th>Matchup</th><th>Projected winner</th><th>Home win %</th><th>Margin (home)</th><th>Confidence</th></tr></thead><tbody>{predictions.map(p => <tr key={p.game_id}><td>{p.week}</td><td className="team">{p.away} <span className="muted">@</span> {p.home}</td><td className="emphasis">{p.predicted_winner}</td><td>{pct(p.home_win_probability)}</td><td>{p.home_margin > 0 ? '+' : ''}{num(p.home_margin)}</td><td>{p.confidence}</td></tr>)}</tbody></table>}</div>
      <footer>Model estimates are probabilistic, not guarantees. Data source: {report.source || 'CFBD'}.</footer>
    </>}
  </main>
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><App /></React.StrictMode>)
