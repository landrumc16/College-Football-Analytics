import { useEffect, useState } from 'react'

type WindowScore = { rank: number | null; strength: number | null; seasons_available: number; seasons_required: number }
type History = { team: string; program_rankings: Record<string, WindowScore> | null; trajectory: { long_term: { classification: string }; recent: { classification: string } } | null; hype: Record<string, { historical_tendency: string; dropped_out: number; entered_top25: number }> }
type HistoryPayload = { schema_version: number; status: string; programs: History[] }
type Team = { team: string; rank: number; rating: number; wins: number; losses: number; projected_wins: number }
type Poll = { ap_top25: { team: string; rank: number }[]; coaches_top25: { team: string; rank: number }[] }
type Cfp = { team: string; cfp_field: number; national_title: number }
type ScheduleGame = { game_id: number; week: number; home: string; away: string; completed: boolean; home_score: number | null; away_score: number | null }
type Prediction = { game_id: number; home: string; away: string; predicted_winner: string; home_win_probability: number; confidence: string }
type Recruiting = { team: string; heldout_seasons: number; average_wins_above_recruiting_baseline: number }

const label = (value: string | undefined) => value?.replaceAll('_', ' ') || 'Unavailable'

export default function TeamProfile({ team, rankings, poll, cfp, schedule, predictions, recruiting, onChoose }: {
  team: string; rankings: Team[]; poll: Poll | null; cfp: Cfp[];
  schedule: ScheduleGame[]; predictions: Prediction[]; recruiting: Recruiting[];
  onChoose: (team: string) => void;
}) {
  const [history, setHistory] = useState<HistoryPayload | null>(null)
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v4-program-intelligence.json', { cache: 'no-store' })
      .then(r => { if (!r.ok) throw new Error('Not published'); return r.json() })
      .then((data: HistoryPayload) => {
        if (active && data.schema_version === 1 && data.status === 'descriptive_only' && Array.isArray(data.programs)) setHistory(data)
      }).catch(() => { /* Historical metrics remain explicitly unavailable. */ })
    return () => { active = false }
  }, [])
  const current = rankings.find(r => r.team === team)
  const historical = history?.programs.find(r => r.team === team)
  const playoff = cfp.find(r => r.team === team)
  const recruitingRecord = recruiting.find(r => r.team === team)
  const games = schedule.filter(g => g.home === team || g.away === team).sort((a, b) => a.week - b.week)
  const predicted = new Map(predictions.map(p => [p.game_id, p]))
  const ap = poll?.ap_top25.find(r => r.team === team)?.rank
  const coaches = poll?.coaches_top25.find(r => r.team === team)?.rank
  const tile = (name: string, value: string) => <div className="team-profile-tile" key={name}><small>{name}</small><strong>{value}</strong></div>
  return <section className="notice">
    <h2>Team Profile</h2>
    <label>Choose school <select value={team} onChange={e => onChoose(e.target.value)}>
      <option value="">Select a program</option>{rankings.map(r => <option key={r.team} value={r.team}>{r.team}</option>)}
    </select></label>
    {team && <><h3>{team}</h3><div className="team-profile-grid">
      {tile('Current Model Rank', current ? '#' + current.rank : 'Unavailable')}
      {tile('Current Strength', current ? current.rating.toFixed(1) : 'Unavailable')}
      {tile('Record', current ? current.wins + '–' + current.losses : 'Unavailable')}
      {tile('Projected Wins', current ? current.projected_wins.toFixed(1) : 'Unavailable')}
      {tile('AP Poll', ap ? '#' + ap : 'Unranked / unavailable')}
      {tile('Coaches Poll', coaches ? '#' + coaches : 'Unranked / unavailable')}
      {tile('10-Year Program Rank', historical?.program_rankings?.['10']?.rank ? '#' + historical.program_rankings['10'].rank : 'Insufficient data')}
      {tile('5-Year Program Rank', historical?.program_rankings?.['5']?.rank ? '#' + historical.program_rankings['5'].rank : 'Insufficient data')}
      {tile('3-Year Program Rank', historical?.program_rankings?.['3']?.rank ? '#' + historical.program_rankings['3'].rank : 'Insufficient data')}
      {tile('10-Year Trajectory', label(historical?.trajectory?.long_term.classification))}
      {tile('3-Year Momentum', label(historical?.trajectory?.recent.classification))}
      {tile('AP Hype Index', label(historical?.hype.AP?.historical_tendency))}
      {tile('Coaches Hype Index', label(historical?.hype.Coaches?.historical_tendency))}
      {tile('Recruiting Development', recruitingRecord ? recruitingRecord.average_wins_above_recruiting_baseline.toFixed(2) + ' wins vs talent baseline' : 'Insufficient research')}
      {tile('CFP Field Odds', playoff ? (playoff.cfp_field * 100).toFixed(1) + '%' : 'Unavailable')}
      {tile('National Title Odds', playoff ? (playoff.national_title * 100).toFixed(1) + '%' : 'Unavailable')}
    </div>
    <details><summary>Full Season Schedule and Model Outlook</summary>
      <p>Completed games show actual scores; future games show the existing published model forecast only when one is available.</p>
      <div className="table-wrap"><table><thead><tr><th>Week</th><th>Opponent</th><th>Result / forecast</th></tr></thead><tbody>{games.map(g => {
        const opponent = g.home === team ? g.away : g.home
        const p = predicted.get(g.game_id)
        const outcome = g.completed && g.home_score != null && g.away_score != null
          ? g.home + ' ' + g.home_score + '–' + g.away_score + ' ' + g.away
          : p ? p.predicted_winner + ' favored · ' + (100 * (p.home === team ? p.home_win_probability : 1 - p.home_win_probability)).toFixed(1) + '% ' + team + ' win probability' : 'Forecast unavailable'
        return <tr key={g.game_id}><td>{g.week}</td><td>{opponent}</td><td>{outcome}</td></tr>
      })}</tbody></table></div>
      {!games.length && <p>No published games for this program.</p>}
    </details>
    <p>Historical rankings, trajectory, and poll expectations are descriptive only. Missing verified seasons are not estimated. Poll status may be unavailable when no current snapshot is published.</p>
    </>}
  </section>
}
