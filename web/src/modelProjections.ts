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
  official: { cfp_field: number; conference_title: number } | null
  tiebreak_swaps?: { rival: string; standard_gap: number; momentum_gap: number }[] }
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

/** Signed margin from one team's point of view, as words: "Texas Tech by 2.3" or "even". */
function margin(g: ProjectedGame, k: ModelKey) {
  const m = g[k].home_margin
  return Math.abs(m) < 0.05 ? 'even' : `${m > 0 ? g.home : g.away} by ${Math.abs(m).toFixed(1)}`
}
const signed = (v: number) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(1)}`

export type Explanation = { summary: string; details: string[] }

/**
 * Why the two models disagree, from published numbers only. Momentum weights recent games more, so the gap follows
 * whichever team's last three games (opponent-adjusted) sit furthest from its full-season rating. Only an explanation
 * consistent with the direction of the gap is offered. The summary is one short sentence; the calculation is in details.
 */
export function disagreement(g: ProjectedGame, data: DualProjections): Explanation {
  const shift = g.momentum.home_margin - g.standard.home_margin
  const details = [`Standard margin: ${margin(g, 'standard')}. Momentum margin: ${margin(g, 'momentum')}.`]
  const formOf = (team: string) => (team === g.home ? g.home_form : g.away_form)
  const seasonOf = (team: string) => data.teams[team]?.standard.rating ?? null
  for (const team of [g.away, g.home]) {
    const f = formOf(team), r = seasonOf(team)
    if (f != null && r != null) details.push(`${team}: last three games ${signed(f)} per game vs a season rating of ${signed(r)} (opponent-adjusted).`)
  }
  details.push('Momentum counts each earlier game 10% less than the one after it; Standard counts every game equally.')
  if (Math.abs(shift) < 1) return { summary: 'The models agree to within a point.', details }
  const helped = shift > 0 ? g.home : g.away
  const by = `Momentum favors ${helped} by ${Math.abs(shift).toFixed(1)} additional points`
  // A home surge or an away slump helps the home side (and vice versa).
  const driver = [g.home, g.away].map(team => {
    const f = formOf(team), r = seasonOf(team)
    return { team, delta: f != null && r != null ? f - r : null }
  }).filter(c => c.delta != null && Math.sign(c.delta) === Math.sign(shift) * (c.team === g.home ? 1 : -1))
    .sort((a, b) => Math.abs(b.delta!) - Math.abs(a.delta!))[0]
  if (!driver) return { summary: `${by} because recent games count more.`, details }
  return { summary: driver.team === helped
    ? `${by} based on stronger recent opponent-adjusted performance.`
    : `${by} based on ${driver.team}'s weaker recent opponent-adjusted performance.`, details }
}

/**
 * One sentence when a team's conference and CFP odds differ between models mainly because it swaps rating order with a
 * same-conference contender (the shared simulation breaks tied conference records by model rating).
 */
export function tiebreakNote(team: string, t: TeamProjection): string | null {
  const swaps = t.tiebreak_swaps ?? []
  if (!swaps.length) return null
  const rivals = swaps.map(s => s.rival)
  const list = rivals.length === 1 ? rivals[0] : `${rivals.slice(0, -1).join(', ')} and ${rivals[rivals.length - 1]}`
  return `Playoff odds differ partly because ${team} and ${list} swap order between the models, and tied conference records go to the higher-rated team.`
}

/** Most likely final record from a win distribution (ties go to the higher win total). */
export function likelyRecord(t: TeamProjection, k: ModelKey) {
  const dist = t[k].win_distribution
  let best = 0
  dist.forEach((q, i) => { if (q >= dist[best]) best = i })
  return { wins: t.wins + best, losses: t.losses + (dist.length - 1 - best), probability: dist[best] }
}

export const weeks = (data: DualProjections) => [...new Set(data.games.map(g => g.week))].sort((a, b) => a - b)
