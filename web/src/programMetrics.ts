/** Shared, descriptive program indicators. No inferred weekly rating snapshots. */
export type CompletedGame = { week: number; home: string; away: string; completed: boolean; home_score: number | null; away_score: number | null }
export type TrackedPerformance = { actual_wins: number; expected_wins: number; games_with_forecasts: number; wins_above_expected: number | null }

export function recentForm(schedule: CompletedGame[], team: string, limit = 5) {
  const games = schedule.filter(g => g.completed && (g.home === team || g.away === team) &&
    Number.isInteger(g.week) && g.home_score != null && g.away_score != null &&
    Number.isFinite(g.home_score) && Number.isFinite(g.away_score))
    .sort((a, b) => b.week - a.week).slice(0, limit)
  const wins = games.filter(g => (g.home === team ? g.home_score! > g.away_score! : g.away_score! > g.home_score!)).length
  const ties = games.filter(g => g.home_score === g.away_score).length
  return { count: games.length, wins, losses: games.length - wins - ties, ties }
}

export function trackedWinsAboveExpected(p?: TrackedPerformance): number | null {
  return p && p.games_with_forecasts >= 3 && p.wins_above_expected != null &&
    Number.isFinite(p.wins_above_expected) ? p.wins_above_expected : null
}

/** Current-rank quality wins: opponents ranked today, never represented as kickoff rank. */
export function winsVsCurrentTop25(schedule: CompletedGame[], team: string, rankings: { team: string; rank: number }[]): number {
  const ranked = new Set(rankings.filter(r => Number.isInteger(r.rank) && r.rank >= 1 && r.rank <= 25).map(r => r.team))
  return schedule.filter(g => g.completed && (g.home === team || g.away === team) &&
    g.home_score != null && g.away_score != null &&
    Number.isFinite(g.home_score) && Number.isFinite(g.away_score) &&
    ranked.has(g.home === team ? g.away : g.home) &&
    (g.home === team ? g.home_score > g.away_score : g.away_score > g.home_score)).length
}
