// Dual model projections: pure helpers (unit-tested). Values come only from dual-projections.json.

export type ModelKey = 'standard' | 'momentum'
export type View = 'compare' | ModelKey
export type GameProjection = { home_points: number; away_points: number; home_margin: number; home_win_probability: number }
export type ProjectedGame = {
  game_id: number; week: number; start_date: string | null; home: string; away: string; neutral_site: boolean
  home_fbs: boolean; away_fbs: boolean; home_form: number | null; away_form: number | null
  standard: GameProjection; momentum: GameProjection; official: { home_win_probability: number; home_margin: number } | null
}
export type TeamModel = { expected_wins: number; expected_losses: number; win_distribution: number[]; rating: number | null
  offense: number | null; defense: number | null; conference_title?: number; cfp_field?: number; national_title?: number }
export type TeamProjection = { wins: number; losses: number; remaining: number; standard: TeamModel; momentum: TeamModel
  official: { cfp_field: number; conference_title: number } | null }
type Scores = { brier: number; log_loss: number; winner_accuracy: number; margin_mae: number }
export type DualProjections = {
  season: number; generated_at: string; data_retrieved_at: string | null; status: string
  models: Record<ModelKey, { label: string; weighting: string; decay?: string }>; method: Record<string, string>
  home_field_points: number; scales: Record<ModelKey, number>
  validation: { pooled_2017_2025: Record<string, Scores>; test_2022_2025: Record<string, Scores>; second_half: Record<string, Scores>
    games: number; test_games: number; authentic_2026: Record<string, number>; authentic_2026_games: number
    season_records_mae_wins: Record<string, number> }
  games: ProjectedGame[]; teams: Record<string, TeamProjection>
}

export const pct = (p: number | null | undefined) => (p == null ? 'N/A' : `${Math.round(100 * p)}%`)
export const points = (p: number) => String(Math.round(p))

/** Favoured team and its win probability for one model. */
export function favourite(g: ProjectedGame, k: ModelKey) {
  const p = g[k].home_win_probability
  return p >= 0.5 ? { team: g.home, probability: p } : { team: g.away, probability: 1 - p }
}

/** "Texas Tech 31, Baylor 29" with the projected winner first (ties keep the home team first). */
export function scoreLine(g: ProjectedGame, k: ModelKey) {
  const m = g[k], homeFirst = Math.round(m.home_points) >= Math.round(m.away_points)
  return homeFirst ? `${g.home} ${points(m.home_points)}, ${g.away} ${points(m.away_points)}` : `${g.away} ${points(m.away_points)}, ${g.home} ${points(m.home_points)}`
}

/**
 * Why the two models disagree, from published numbers only: Momentum weights recent games more, so the gap follows
 * whichever team's last three games (opponent-adjusted) sit furthest from its full-season rating.
 */
export function disagreement(g: ProjectedGame, data: DualProjections): string {
  const shift = g.momentum.home_margin - g.standard.home_margin
  if (Math.abs(shift) < 1) return 'The two models agree to within a point: recent games and the full season tell the same story.'
  const helped = shift > 0 ? g.home : g.away
  const formOf = (team: string) => (team === g.home ? g.home_form : g.away_form)
  const seasonOf = (team: string) => data.teams[team]?.standard.rating ?? null
  // A home surge or an away slump helps the home side (and vice versa); only consistent explanations are offered.
  const consistent = [g.home, g.away].map(team => {
    const f = formOf(team), s = seasonOf(team)
    return { team, delta: f != null && s != null ? f - s : null }
  }).filter(c => c.delta != null && Math.sign(c.delta) === Math.sign(shift) * (c.team === g.home ? 1 : -1))
  const driver = consistent.sort((a, b) => Math.abs(b.delta!) - Math.abs(a.delta!))[0]
  const lead = `Momentum favours ${helped} by ${Math.abs(shift).toFixed(1)} more points than Standard.`
  if (!driver) return `${lead} Recent games count more in Momentum, and they lean slightly toward ${helped}.`
  const direction = driver.delta! > 0 ? 'better' : 'worse'
  return `${lead} ${driver.team}'s last three games were ${Math.abs(driver.delta!).toFixed(1)} points per game ${direction} than its season level, after adjusting for opponents.`
}

/** Most likely final record from a win distribution (ties go to the higher win total). */
export function likelyRecord(t: TeamProjection, k: ModelKey) {
  const dist = t[k].win_distribution
  let best = 0
  dist.forEach((q, i) => { if (q >= dist[best]) best = i })
  return { wins: t.wins + best, losses: t.losses + (dist.length - 1 - best), probability: dist[best] }
}

export const weeks = (data: DualProjections) => [...new Set(data.games.map(g => g.week))].sort((a, b) => a - b)
