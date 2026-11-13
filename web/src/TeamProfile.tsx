import ProgramReportCard from './ProgramReportCard'
import HistoricalResults from './HistoricalResults'
import { useEffect, useState } from 'react'
import { isPublishedHistoricalIntelligence } from './historicalPublication'
import { recentForm, trackedWinsAboveExpected, winsVsCurrentTop25, seasonFormTrend } from './programMetrics'

type WindowScore = { rank: number | null; strength: number | null; seasons_available: number; seasons_required: number; years?: number[]; sources?: { season: number; source: string }[] }
type History = { team: string; program_rankings: Record<string, WindowScore> | null; trajectory: { long_term: { classification: string }; medium_term?: { classification: string }; recent: { classification: string } } | null; hype: Record<string, { historical_tendency: string; dropped_out: number; entered_top25: number }> }
type HistoryPayload = { schema_version: number; status: string; programs: History[] }
type Team = { team: string; rank: number; rating: number; wins: number; losses: number; projected_wins: number }
type Poll = { ap_top25: { team: string; rank: number }[]; coaches_top25: { team: string; rank: number }[] }
type Cfp = { team: string; cfp_field: number; national_title: number }
type ScheduleGame = { game_id: number; week: number; home: string; away: string; completed: boolean; home_score: number | null; away_score: number | null }
type Prediction = { game_id: number; home: string; away: string; predicted_winner: string; home_win_probability: number; confidence: string; home_margin?: number }
type ModelMetadata = { prediction_scale: number; home_field_advantage: number; model_status: string }
type Recruiting = { team: string; heldout_seasons: number; average_wins_above_recruiting_baseline: number }
type Performance = { actual_wins: number; expected_wins: number; games_with_forecasts: number; wins_above_expected: number | null }
type ConferenceTeam = { team: string; conference_title_odds: number; conference_wins: number; conference_losses: number }

const label = (value: string | undefined) => value?.replaceAll('_', ' ') || 'Unavailable'
/** Only use a forecast when its game ID and both opponents match the schedule. */
const matchingForecast = (predictions: Prediction[], game: ScheduleGame): Prediction | null => {
  if (game.completed) return null
  const matches = predictions.filter(p => p.game_id === game.game_id)
  if (matches.length !== 1) return null
  const p = matches[0]
  if (p.home !== game.home || p.away !== game.away ||
      !Number.isFinite(p.home_win_probability) ||
      p.home_win_probability < 0 || p.home_win_probability > 1 ||
      (p.predicted_winner !== p.home && p.predicted_winner !== p.away) ||
      (p.predicted_winner === p.home && p.home_win_probability < 0.5) ||
      (p.predicted_winner === p.away && p.home_win_probability > 0.5) ||
      (p.home_margin != null && (!Number.isFinite(p.home_margin) ||
        (p.predicted_winner === p.home && p.home_margin < 0) ||
        (p.predicted_winner === p.away && p.home_margin > 0)))) return null
  return p
}

const predictedForecast = (predictions: Prediction[], game: ScheduleGame, team: string): number | null => {
  const p = matchingForecast(predictions, game)
  if (!p || (team !== game.home && team !== game.away)) return null
  return p.home === team ? p.home_win_probability : 1 - p.home_win_probability
}

export default function TeamProfile({ team, rankings, poll, cfp, schedule, predictions, recruiting, performance, conferences, modelMetadata, onChoose, onCompare }: {
  team: string; rankings: Team[]; poll: Poll | null; cfp: Cfp[];
  schedule: ScheduleGame[]; predictions: Prediction[]; recruiting: Recruiting[];
  performance: Record<string, Performance>; conferences: Record<string, ConferenceTeam[]>; modelMetadata?: ModelMetadata;
  onChoose: (team: string) => void; onCompare: (team: string) => void;
}) {
  const [history, setHistory] = useState<HistoryPayload | null>(null)
  const [historyStatus, setHistoryStatus] = useState<'loading' | 'published' | 'unavailable'>('loading')
  useEffect(() => {
    let active = true
    fetch(import.meta.env.BASE_URL + 'v4-program-intelligence.json', { cache: 'no-store' })
      .then(r => { if (!r.ok || !r.headers.get('content-type')?.includes('json')) throw new Error('Not published'); return r.json() })
      .then((data: HistoryPayload) => {
        if (active) {
          if (isPublishedHistoricalIntelligence(data)) { setHistory(data); setHistoryStatus('published') }
          else setHistoryStatus('unavailable')
        }
      }).catch(() => { if (active) setHistoryStatus('unavailable') })
    return () => { active = false }
  }, [])
  const current = rankings.find(r => r.team === team)
  const historical = history?.programs.find(r => r.team === team)
  const playoff = cfp.find(r => r.team === team)
  const recruitingRecord = recruiting.find(r => r.team === team)
  const performanceRecord = performance[team]
  const lastFive = recentForm(schedule, team)
  const seasonTrend = seasonFormTrend(schedule, team)
  const winsAgainstCurrentTop25 = winsVsCurrentTop25(schedule, team, rankings)
  const forecastGap = trackedWinsAboveExpected(performanceRecord)
  const conference = Object.entries(conferences).find(([, rows]) => rows.some(row => row.team === team))
  const conferenceTeam = conference?.[1].find(row => row.team === team)
  const resultsVsForecast = forecastGap == null ? 'Insufficient tracked forecasts' : forecastGap >= 1 ? 'Outperforming forecast' : forecastGap <= -1 ? 'Underperforming forecast' : 'Near expectation'
  const playoffOutlook = playoff?.cfp_field == null ? 'Insufficient simulation data' : playoff.cfp_field >= 0.5 ? 'Playoff contender' : playoff.cfp_field >= 0.15 ? 'On the bubble' : 'Outside current projection'
  const upcoming = schedule.filter(g => !g.completed && (g.home === team || g.away === team))
  const upcomingForecasts = upcoming.map(g => predictedForecast(predictions, g, team)).filter((p): p is number => p !== null)
  const forecastConfidence = upcomingForecasts.length ? Math.max(...upcomingForecasts.map(p => Math.max(p, 1 - p))) : null
  const opponentStrength = upcoming.map(g => ({ opponent: g.home === team ? g.away : g.home, rank: rankings.find(r => r.team === (g.home === team ? g.away : g.home))?.rank }))
  const rankedOpponents = opponentStrength.filter(g => g.rank != null).sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity))
  const games = schedule.filter(g => g.home === team || g.away === team).sort((a, b) => a.week - b.week)
  const ap = poll?.ap_top25.find(r => r.team === team)?.rank
  const coaches = poll?.coaches_top25.find(r => r.team === team)?.rank
  const tile = (name: string, value: string) => <div className="team-profile-tile" key={name}><small>{name}</small><strong>{value}</strong></div>
  return <section className="notice">
    <h2>Team Profile</h2><button type="button" onClick={() => onCompare(team)} disabled={!team}>Compare this school</button>
    <label>Choose school <select value={team} onChange={e => onChoose(e.target.value)}>
      <option value="">Select a program</option>{rankings.map(r => <option key={r.team} value={r.team}>{r.team}</option>)}
    </select></label>
    {team && <><h3>{team}</h3><ProgramReportCard team={team} /><HistoricalResults team={team} onTeam={onChoose} /><div className="team-profile-grid">
      {tile('Current Model Rank', current ? '#' + current.rank : 'Unavailable')}
      {tile('Current Strength', current ? current.rating.toFixed(1) : 'Unavailable')}
      {tile('Record', current ? current.wins + '–' + current.losses : 'Unavailable')}
      {tile('Projected Wins', current ? current.projected_wins.toFixed(1) : 'Unavailable')}
      {tile('AP Poll', !poll ? 'Poll unavailable' : ap ? '#' + ap : 'Unranked')}
      {tile('Coaches Poll', !poll ? 'Poll unavailable' : coaches ? '#' + coaches : 'Unranked')}
      {tile('Wins vs Current Model Top 25', schedule.some(g => g.completed && (g.home === team || g.away === team) && g.home_score != null && g.away_score != null) ? String(winsAgainstCurrentTop25) : 'No scored games')}
      {tile('Last Five Completed Games', lastFive.count ? `${lastFive.wins}–${lastFive.losses} (${lastFive.count} games)` : 'No scored games')}
      {tile('Current-Season Form Trend', seasonTrend ?? 'Requires 8 scored games')}
      {tile('Conference', conference?.[0] || 'Unavailable')}
      {tile('Conference Record', conferenceTeam ? `${conferenceTeam.conference_wins}–${conferenceTeam.conference_losses}` : 'Unavailable')}
      {tile('Results vs Forecast', resultsVsForecast)}
      {tile('Current CFP Outlook', playoffOutlook)}
      {tile('Upcoming Matchup Confidence', forecastConfidence == null ? 'No upcoming forecast' : (forecastConfidence * 100).toFixed(1) + '% strongest pick confidence')}
      {tile('Strongest Remaining Opponent', rankedOpponents.length ? '#' + rankedOpponents[0].rank + ' ' + rankedOpponents[0].opponent : 'Unavailable')}
      {tile('Wins vs Model Expectation', forecastGap == null ? 'Insufficient forecasts' : (forecastGap > 0 ? '+' : '') + forecastGap.toFixed(2))}
      {tile('Conference Title Odds', conferenceTeam ? (100 * conferenceTeam.conference_title_odds).toFixed(1) + '%' : 'Unavailable')}
      {tile('Recruiting Development', recruitingRecord ? recruitingRecord.average_wins_above_recruiting_baseline.toFixed(2) + ' wins vs talent baseline' : 'Insufficient research')}
      {tile('CFP Field Odds', playoff ? (playoff.cfp_field * 100).toFixed(1) + '%' : 'Unavailable')}
      {tile('National Title Odds', playoff ? (playoff.national_title * 100).toFixed(1) + '%' : 'Unavailable')}
    </div>
    <div className="accuracy-summary"><h3>Program development and expectations</h3>
      <p>Last five completed games: {lastFive.count ? `${lastFive.wins} wins, ${lastFive.losses} losses across ${lastFive.count} games` : 'No completed scored games available'}. Current-season form trend: {seasonTrend ?? 'not enough scored games'} (two non-overlapping four-game windows, requiring a two-win difference to classify a change). This describes results, not a measured change in team strength. Wins against the current model Top 25 use today's opponent rankings, not their ranking at kickoff.</p>
      <p><strong>Against forecasts:</strong> {resultsVsForecast}{forecastGap == null ? '.' : ` (${forecastGap > 0 ? '+' : ''}${forecastGap.toFixed(2)} wins across ${performanceRecord?.games_with_forecasts ?? 0} tracked games).`}</p>
      <p><strong>Long-term trajectory:</strong> {historical?.trajectory?.recent.classification ? label(historical.trajectory.recent.classification) : 'Not published with verified multi-season coverage'}.</p>
      <p>AP/Coaches historical expectations: {historical?.hype.AP?.historical_tendency ? label(historical.hype.AP.historical_tendency) : 'Not yet verified'}; current poll positions are separate from preseason expectations.</p>
    </div>
    <details><summary>Historical program ranking coverage and sources</summary>
      <p role="status">{historyStatus === 'published' ? 'Independently reviewed historical research is published.' : historyStatus === 'loading' ? 'Checking historical publication status…' : 'Historical research has not passed the publication gate; rankings, trajectory, and hype remain unavailable.'}</p>
      <p>Historical rankings are descriptive, not forecasts. A ranking requires verified opponent-adjusted strengths for every completed season in its window. Missing seasons are not imputed.</p>
      <div className="table-wrap"><table><thead><tr><th>Window</th><th>Rank</th><th>Coverage</th><th>Years available</th><th>Source evidence</th></tr></thead><tbody>{(['10', '5', '3'] as const).map(window => {
        const score = historical?.program_rankings?.[window]
        return <tr key={window}><td>{window} seasons</td><td>{score?.rank == null ? 'Unavailable' : '#' + score.rank}</td><td>{score ? score.seasons_available + '/' + score.seasons_required : 'Unavailable'}</td><td>{score?.years?.join(', ') || 'Unavailable'}</td><td>{score?.sources?.length ? <details><summary>{score.sources.length} sourced seasons</summary><ul>{score.sources.map(source => <li key={source.season}>{source.season}: {source.source}</li>)}</ul></details> : 'No reviewed source records published'}</td></tr>
      })}</tbody></table></div>
    </details>
    <details><summary>Coaching, roster and matchup data availability</summary><p>Verified season-specific head-coach and coordinator records, transfer and returning-production data, and offense-versus-defense matchup factors have not been published for this profile. They are not silently estimated or treated as inputs to the incumbent prediction engine.</p></details>
    <details><summary>Remaining opponent strength</summary><p>Upcoming opponents are ordered by the current model ranking. This is a schedule-context indicator, not a verified historical strength-of-schedule adjustment.</p><ol>{rankedOpponents.map(g => <li key={g.opponent}>#{g.rank} {g.opponent}</li>)}</ol></details>
    <details><summary>CFP outlook and confidence methodology</summary><p>Current CFP Outlook reflects published CFP simulation probabilities, not a separately verified Contenders & Pretenders assessment. That feature remains unavailable pending its approved evidence-backed classification. Upcoming confidence is the highest favored-side win probability among available future-game forecasts; it does not imply calibration or guarantee outcomes.</p></details>
    <details><summary>Stock Watch and results versus forecast</summary><p>The approved Team Stock Watch requires a verified 0–100 time-aware index and a four-week change. Neither is inferred from season-total wins above expectation. Results versus Forecast separately compares actual wins with the published model’s expected wins for games with forecasts; at least three forecasted games are required. It is descriptive, not a validated trajectory signal.</p></details>
    <details><summary>Upcoming prediction explanations</summary>
      <p>Published model probabilities are shown alongside the current rating comparison. Ratings and home-field advantage provide context, not an audited feature-level attribution. Coaching, roster, and matchup-specific contributions remain unavailable until validated.</p>
      <div className="table-wrap"><table><thead><tr><th>Week</th><th>Matchup</th><th>Team win probability</th><th>Current rating gap</th><th>Forecast</th></tr></thead><tbody>{upcoming.map(g => {
        const opponent = g.home === team ? g.away : g.home
        const forecast = matchingForecast(predictions, g)
        const ourRating = rankings.find(r => r.team === team)?.rating
        const theirRating = rankings.find(r => r.team === opponent)?.rating
        const gap = ourRating == null || theirRating == null ? null : ourRating - theirRating
        const probability = predictedForecast(predictions, g, team)
        return <tr key={g.game_id}><td>{g.week}</td><td>{g.away} at {g.home}</td><td>{probability == null ? "Unavailable" : (probability * 100).toFixed(1) + "%"}</td><td>{gap == null ? "Unavailable" : (gap > 0 ? "+" : "") + gap.toFixed(1)}</td><td>{forecast?.confidence || "Unavailable"}</td></tr>
      })}</tbody></table></div>
      {!upcoming.length && <p>No remaining scheduled games.</p>}
      <p>Model status: {modelMetadata?.model_status || 'Not published'}. Home-field setting: {modelMetadata?.home_field_advantage ?? 'Unavailable'} rating points. Rating scale: {modelMetadata?.prediction_scale ?? 'Unavailable'}.</p>
    </details>
    <details><summary>Full Season Schedule and Model Outlook</summary>
      <p>Completed games show actual scores; future games show the existing published model forecast only when one is available.</p>
      <div className="table-wrap"><table><thead><tr><th>Week</th><th>Opponent</th><th>Result / forecast</th></tr></thead><tbody>{games.map(g => {
        const opponent = g.home === team ? g.away : g.home
        const p = matchingForecast(predictions, g)
        const outcome = g.completed && g.home_score != null && g.away_score != null && Number.isFinite(g.home_score) && Number.isFinite(g.away_score)
          ? g.home + ' ' + g.home_score + '–' + g.away_score + ' ' + g.away
          : g.completed ? 'Final score unavailable' : p ? p.predicted_winner + ' favored · ' + (100 * (p.home === team ? p.home_win_probability : 1 - p.home_win_probability)).toFixed(1) + '% ' + team + ' win probability' : 'Forecast unavailable'
        return <tr key={g.game_id}><td>{g.week}</td><td>{opponent}</td><td>{outcome}</td></tr>
      })}</tbody></table></div>
      {!games.length && <p>No published games for this program.</p>}
    </details>
    <p>Historical rankings, trajectory, and poll expectations are descriptive only. Missing verified seasons are not estimated. Poll status may be unavailable when no current snapshot is published.</p>
    </>}
  </section>
}
