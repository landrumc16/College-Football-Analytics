/**
 * Descriptive three-score team strength (Season Strength, Recent Momentum, Combined Strength).
 * Mirrors scripts/strength_blend_research.calculate_strength_components on published report data.
 * Never feeds the official forecast, rankings, playoff odds or Market calculator.
 */
export const MOMENTUM_GAMES = 3
export const MOMENTUM_WEIGHT = 0.2        // best tested weight (2022-2025 replay); 65/35 performed worse
export const STEADY_BAND = 1.0            // rating points; smaller differences read as "steady"
const HOME_EDGE = 3, MARGIN_CAP = 45, FCS_RATING = -26

export type ScoreGame = { week: number; home: string; away: string; completed: boolean; home_score: number | null; away_score: number | null; game_id?: number }
export type StrengthScores = {
  season: number; momentum: number | null; combined: number; momentumGames: number
  direction: 'rising' | 'steady' | 'declining' | 'insufficient_data'
}

/** Engine-identical adjusted margin: home edge always removed (workbook rule), capped at +/-45. */
export const adjustedHomeMargin = (home: number, away: number) => Math.max(-MARGIN_CAP, Math.min(MARGIN_CAP, home - away - HOME_EDGE))

export function strengthScores(team: string, seasonRating: number, ratings: Record<string, number>, schedule: ScoreGame[],
  window = MOMENTUM_GAMES, weight = MOMENTUM_WEIGHT): StrengthScores | null {
  if (!Number.isFinite(seasonRating)) return null
  const played = schedule
    .filter(g => g.completed && (g.home === team || g.away === team) && Number.isFinite(g.home_score) && Number.isFinite(g.away_score) && g.home_score !== null && g.away_score !== null)
    .sort((a, b) => a.week - b.week || (a.game_id ?? 0) - (b.game_id ?? 0))
  if (played.length < window) return { season: seasonRating, momentum: null, combined: seasonRating, momentumGames: played.length, direction: 'insufficient_data' }
  const observations = played.slice(-window).map(g => {
    const home = g.home === team
    const opponent = home ? g.away : g.home
    const adjusted = adjustedHomeMargin(g.home_score as number, g.away_score as number)
    return (ratings[opponent] ?? FCS_RATING) + (home ? adjusted : -adjusted)
  })
  const momentum = observations.reduce((s, x) => s + x, 0) / observations.length
  const delta = momentum - seasonRating
  return {
    season: seasonRating, momentum, combined: (1 - weight) * seasonRating + weight * momentum, momentumGames: window,
    direction: delta > STEADY_BAND ? 'rising' : delta < -STEADY_BAND ? 'declining' : 'steady',
  }
}
