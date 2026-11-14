import type { ReactNode } from 'react'
import { destinations } from './Navigation'
import { useReportCards } from './ProgramReportCard'
import './editorial-preview.css'

type Team = { team: string; rank: number; wins: number; losses: number }
type Game = { game_id: number; week: number; home: string; away: string; predicted_winner: string; home_win_probability: number; home_margin: number }
type HomeReport = {
  season: number; retrieved_at?: string | null; rankings: Team[];
  projected_bracket?: { seeds: { seed: number; team: string }[] };
  cfp?: { teams: { team: string; cfp_field: number }[] };
}
const percent = (value: number) => `${(100 * value).toFixed(1)}%`

function DestinationIcon({ destination }: { destination: string }) {
  const paths: Record<string, string> = {
    home: 'M3 10 12 3l9 7v11h-6v-7H9v7H3Z',
    rankings: 'M4 21V12h4v9M10 21V3h4v18M16 21V8h4v13',
    teams: 'M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6ZM8 11h8M12 7v8',
    playoffs: 'M8 3h8v7a4 4 0 0 1-8 0ZM8 5H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4m-4 2v6m-4 1h8',
    research: 'M12 5C9 3 5 3 3 4v15c3-1 6-1 9 1m0-15c3-2 7-2 9-1v15c-3-1-6-1-9 1Z',
  }
  return <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"><path d={paths[destination]} /></svg>
}

export function EditorialMasthead({ children }: { children: ReactNode }) {
  return <header className="editorial-masthead">
    <img src={`${import.meta.env.BASE_URL}icons/icon-192.png`} alt="College Football Analytics collegiate logo" width="48" height="48" />
    <h1>College Football <span>Analytics</span></h1>
    <details className="editorial-menu"><summary aria-label="App menu">Menu <span aria-hidden="true">☰</span></summary><div>{children}</div></details>
  </header>
}

export function EditorialNavigation({ destination, onChange }: { destination: string; onChange: (id: string) => void }) {
  return <nav className="editorial-navigation" aria-label="Main navigation">
    {destinations.map(item => <button key={item.id} type="button" aria-current={destination === item.id ? 'page' : undefined} onClick={() => onChange(item.id)}>
      <DestinationIcon destination={item.id} /><span>{item.label}</span>
    </button>)}
  </nav>
}

export default function EditorialHome({ report, games, favorites, poll, favoriteControls, onGame, onTeam, onRankings, onPlayoffs, onSpotlight, onAllGames }: {
  report: HomeReport; games: Game[]; favorites: (string | null)[];
  poll: { season: number; ap_top25: { team: string; rank: number }[] } | null;
  favoriteControls: ReactNode; onGame: (game: Game) => void; onTeam: (team: string) => void;
  onRankings: () => void; onPlayoffs: () => void; onSpotlight: (team: string) => void; onAllGames: () => void;
}) {
  const cards = useReportCards()
  const nextWeek = games.length ? Math.min(...games.map(game => game.week)) : null
  const rank = (team: string) => report.rankings.find(row => row.team === team)?.rank
  const featured = games.filter(game => game.week === nextWeek)
    .sort((a,b) => Number((rank(b.home) ?? 999) <= 25 && (rank(b.away) ?? 999) <= 25) - Number((rank(a.home) ?? 999) <= 25 && (rank(a.away) ?? 999) <= 25)
      || Math.abs(a.home_win_probability - .5) - Math.abs(b.home_win_probability - .5)).slice(0,3)
  const topFive = [...report.rankings].sort((a,b) => a.rank-b.rank).slice(0,5)
  const disagreement = poll?.season === report.season ? poll.ap_top25.map(row => ({ ...row, model: rank(row.team) }))
    .filter((row): row is typeof row & { model: number } => row.model !== undefined)
    .sort((a,b) => Math.abs(b.rank-b.model)-Math.abs(a.rank-a.model))[0] : null
  const seeds = [...(report.projected_bracket?.seeds || [])].sort((a,b) => a.seed-b.seed)
  const bubble = report.cfp?.teams.filter(team => !seeds.some(seed => seed.team === team.team)).sort((a,b) => b.cfp_field-a.cfp_field)[0]
  // Choose an existing reviewed finding; do not create a score or a new classification.
  const spotlight = cards?.coverage.trajectory.national_grades_available ? cards.programs.filter(program => program.trajectory?.direction === 'rising' && program.categories.trajectory.score !== null)
    .sort((a,b) => Number(favorites.includes(b.team))-Number(favorites.includes(a.team)) || (b.trajectory?.value ?? 0)-(a.trajectory?.value ?? 0))[0] : null
  const saved = favorites.filter((team): team is string => team !== null)
  return <div className="editorial-home">
    <div className="editorial-lede"><p className="editorial-kicker">THE WEEK AHEAD</p><h2>This week in college football.</h2>
      <p>{report.season} season{nextWeek !== null ? ` · Week ${nextWeek}` : ''}{report.retrieved_at ? ` · Checked ${new Date(report.retrieved_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}` : ''}</p>
    </div>
    <section className="editorial-featured" aria-labelledby="featured-heading">
      <div className="editorial-section-heading"><h2 id="featured-heading">Featured Matchups</h2><button type="button" onClick={onAllGames}>All games <span aria-hidden="true">↗</span></button></div>
      <div className="editorial-game-grid">{featured.map((game,index) => <button className={`editorial-game ${index === 2 ? 'editorial-third-game' : ''}`} key={game.game_id} onClick={() => onGame(game)}>
        <span className="editorial-game-kicker">{rank(game.home) && rank(game.home)! <= 25 && rank(game.away) && rank(game.away)! <= 25 ? 'MODEL TOP 25 MATCHUP' : `WEEK ${game.week}`}</span>
        <strong><span>#{rank(game.away) ?? '—'} {game.away}</span><small>at</small><span>#{rank(game.home) ?? '—'} {game.home}</span></strong>
        <span className="editorial-pick">{game.predicted_winner} <b>{percent(game.predicted_winner === game.home ? game.home_win_probability : 1-game.home_win_probability)}</b><span aria-hidden="true"> →</span></span>
        <span className="editorial-game-note">{Math.abs(game.home_margin).toFixed(1)}-point projected margin</span>
      </button>)}</div>
      {!featured.length && <p>No upcoming games in the published report.</p>}
    </section>
    <div className="editorial-news-grid">
      <section className="editorial-my-teams" aria-labelledby="my-teams-heading"><div className="editorial-section-heading"><h2 id="my-teams-heading">My Teams</h2><details className="editorial-favorite-editor"><summary>Edit teams</summary><div>{favoriteControls}</div></details></div>
        <div>{saved.map(name => {
          const team = report.rankings.find(team => team.team === name)
          const game = games.filter(game => game.home === name || game.away === name).sort((a,b) => a.week-b.week)[0]
          const probability = game ? game.home === name ? game.home_win_probability : 1-game.home_win_probability : null
          return <button className="editorial-team-row" key={name} onClick={() => onTeam(name)} aria-label={`Open ${name} Team Profile`}>
            <span className="editorial-team-identity"><strong>{name}</strong><small>{game ? `${game.home === name ? 'vs.' : 'at'} ${game.home === name ? game.away : game.home}` : 'No upcoming game listed'}</small></span>
            <span className="editorial-team-numbers"><strong>{team ? `#${team.rank} · ${team.wins}–${team.losses}` : 'Unranked'}</strong><small>{probability !== null ? `${percent(probability)} to win` : 'Forecast unavailable'}</small></span><span className="editorial-row-arrow" aria-hidden="true">›</span>
          </button>
        })}</div>
        {!saved.length && <p className="editorial-empty">Save up to three schools using Edit teams.</p>}
      </section>
      <section className="editorial-rankings" aria-labelledby="rankings-heading"><div className="editorial-section-heading"><h2 id="rankings-heading">Rankings Snapshot</h2><button onClick={onRankings}>Full rankings ↗</button></div>
        <ol>{topFive.map(team => <li key={team.team}><button onClick={() => onTeam(team.team)}><span className="editorial-rank">{team.rank}</span><strong>{team.team}</strong><span>{team.wins}–{team.losses}</span></button></li>)}</ol>
        {disagreement && <p className="editorial-disagreement"><strong>Different reads.</strong> {disagreement.team}: AP #{disagreement.rank}, model #{disagreement.model}.</p>}
      </section>
      <section className="editorial-playoffs" aria-labelledby="playoffs-heading"><div className="editorial-section-heading"><h2 id="playoffs-heading">Playoff Watch</h2><button onClick={onPlayoffs}>CFP outlook ↗</button></div>
        <button className="editorial-story-link" onClick={onPlayoffs}><small>PROJECTED LEADING SEEDS</small><strong>{seeds.slice(0,4).map(seed => seed.team).join(' · ') || 'Projection unavailable'}</strong>
          {bubble && <span>{bubble.team} leads teams outside the projected field at {percent(bubble.cfp_field)} to qualify.</span>}</button>
      </section>
      <section className="editorial-spotlight" aria-labelledby="spotlight-heading"><div className="editorial-section-heading"><h2 id="spotlight-heading">Program Spotlight</h2><span className="editorial-verified">VERIFIED HISTORY</span></div>
        {spotlight?.trajectory ? <button className="editorial-story-link" onClick={() => onSpotlight(spotlight.team)}><strong>{spotlight.team} is trending up.</strong><span>FBS win rate: {percent(spotlight.trajectory.windows['3'])} over 3 years, compared with {percent(spotlight.trajectory.windows['10'])} over 10 years.</span><small>2016–2025 archive · 2020 excluded <span aria-hidden="true">↗</span></small></button> : <p className="editorial-empty">No reviewed rising-program finding is available.</p>}
      </section>
    </div>
    <p className="editorial-caveat">Model estimates, not guarantees. Rankings are our model; historical trends are descriptive.</p>
  </div>
}
