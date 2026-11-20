// "Why this prediction?" — plain-English explanations built only from prediction-explanations.json (unit-tested).
// Every number is an exact part of a published forecast; schedule and record facts are context, never extra points.

export type Parts = { season_games: number; preseason_prior: number; home_field: number; home_margin: number }
export type DualParts = Parts & { home_points: number; away_points: number; home_offense_vs_away_defense: number
  away_offense_vs_home_defense: number; home_win_probability: number }
export type ExplainedGame = { game_id: number; week: number; home: string; away: string; neutral_site: boolean
  official: Parts; standard: DualParts; momentum: DualParts }
export type WeakestGame = { opponent: string; opponent_fbs: boolean; points_for: number; points_against: number; net_value: number; season_average: number }
export type ExplainedTeam = { wins: number; losses: number; official_rank: number; official_rating: number; official_games_average: number | null
  official_effective_prior: number; schedule_strength: number; schedule_rank: number; schedule_teams: number; quality_wins: number; bad_losses: number
  standard_net_rank: number; momentum_net_rank: number; offense_rank: number; defense_rank: number; fbs_teams: number
  recent_form: number | null; season_game_average: number | null; standard_net: number; momentum_net: number; weakest_game: WeakestGame | null }
export type ExplanationData = { season: number; generated_at: string; data_retrieved_at: string | null; official_home_field: number
  official_prior_games: number; dual_prior_games: number; dual_home_field: number; league_average_points: number
  unavailable: string[]; games: ExplainedGame[]; teams: Record<string, ExplainedTeam> }

export type Contribution = { label: string; points: number }   // points toward the favourite (negative = toward the underdog)
export type ModelRow = { model: string; season: number; prior: number; home: number; total: number }
export type Factor = { key: 'strength' | 'schedule' | 'matchup' | 'recent' | 'home'; title: string; text: string }
export type Explanation = { favourite: string; underdog: string; headline: string; bottomLine: string; factors: Factor[]
  models: ModelRow[]; modelDifference: string; notes: string[]; unavailable: string[] }

const one = (v: number) => Math.abs(v).toFixed(1)
const signed = (v: number) => `${v >= 0 ? '+' : '−'}${one(v)}`
const ordinal = (n: number) => `No. ${n}`
const record = (t: ExplainedTeam) => `${t.wins}–${t.losses}`
const toward = (points: number, fav: string, dog: string) => Math.abs(points) < 0.05 ? 'no effect' : `${one(points)} points toward ${points > 0 ? fav : dog}`
const num = (v: number) => `${v < 0 ? '−' : ''}${Math.abs(v).toFixed(1)}`

/** Official components from the favourite's point of view (sum = favourite's published margin). */
function favParts(p: Parts, favIsHome: boolean) {
  const s = favIsHome ? 1 : -1
  return { season: s * p.season_games, prior: s * p.preseason_prior, home: s * p.home_field, total: s * p.home_margin }
}

/** The one-sentence bottom line, naming the main reason and anything working against the favourite. */
export function bottomLine(fav: string, dog: string, home: string | null, parts: { season: number; prior: number; home: number }) {
  const phrase = (k: 'season' | 'prior' | 'home', team: string) =>
    k === 'season' ? `${team}'s stronger results this season` : k === 'prior' ? `${team}'s carry-over from last season` : `${team}'s home field`
  const keys = (['season', 'prior', 'home'] as const).filter(k => k !== 'home' || home)
  const forFav = keys.filter(k => parts[k] >= 0.5).sort((a, b) => parts[b] - parts[a])
  const against = keys.filter(k => parts[k] <= -0.5).sort((a, b) => parts[a] - parts[b])
  const owner = (k: 'season' | 'prior' | 'home', favSide: boolean) => k === 'home' ? home! : favSide ? fav : dog
  let text = forFav.length ? `${phrase(forFav[0], owner(forFav[0], true))[0].toUpperCase()}${phrase(forFav[0], owner(forFav[0], true)).slice(1)} ${forFav[0] === 'season' ? 'are' : 'is'} the main reason ${fav} is favored`
    : `${fav} is favored by a small combination of factors`
  if (forFav.length > 1) text += `, helped by ${phrase(forFav[1], owner(forFav[1], true))}`
  if (Math.abs(parts.season) < 1 && !forFav.includes('season') && !against.includes('season')) text += '; this season\'s games alone rate the teams almost even'
  if (against.length) text += `; ${against.map(k => `${phrase(k, owner(k, false))} (${one(parts[k])} points)`).join(' and ')} ${against.length > 1 ? 'work' : 'works'} against ${fav}`
  return text + '.'
}

export function explain(g: ExplainedGame, data: ExplanationData): Explanation | null {
  const th = data.teams[g.home], ta = data.teams[g.away]
  if (!th || !ta) return null
  const favIsHome = g.official.home_margin >= 0
  const fav = favIsHome ? g.home : g.away, dog = favIsHome ? g.away : g.home
  const tf = favIsHome ? th : ta, td = favIsHome ? ta : th
  const o = favParts(g.official, favIsHome), s = favParts(g.standard, favIsHome), m = favParts(g.momentum, favIsHome)
  const homeTeam = g.neutral_site ? null : g.home
  const margin = (v: number) => v >= 0.05 ? `${fav} by ${one(v)}` : v <= -0.05 ? `${dog} by ${one(v)}` : 'even'
  const headline = `Official forecast: ${fav} by ${one(o.total)} points. Standard: ${margin(s.total)}. Momentum: ${margin(m.total)}.`

  // 1. Opponent-adjusted strength: this season's games vs last season's carry-over (exact parts of the margin).
  const ga = tf.official_games_average, gd = td.official_games_average
  const seasonView = ga == null || gd == null ? '' : Math.abs(ga - gd) < 0.5
    ? ` On 2026 games alone, after adjusting for opponents, the teams rate almost even (${fav} ${num(ga)}, ${dog} ${num(gd)} per game).`
    : ` On 2026 games alone, after adjusting for opponents, ${ga > gd ? fav : dog} rates higher (${fav} ${num(ga)}, ${dog} ${num(gd)} per game).`
  const strength = `This season's games: ${toward(o.season, fav, dog)}. Carry-over from last season: ${toward(o.prior, fav, dog)}.${seasonView} Each team starts from last season's level, which still counts as ${data.official_prior_games} games in the official model (${data.dual_prior_games} in Standard and Momentum).`

  // 2. Schedule strength and quality wins — context only (already inside the ratings).
  const tougher = tf.schedule_strength === td.schedule_strength ? null : tf.schedule_strength > td.schedule_strength ? fav : dog
  let schedule = `${tougher ? `${tougher} has played the tougher schedule` : 'The schedules rate evenly'}: average opponent rating ${fav} ${num(tf.schedule_strength)} (${ordinal(tf.schedule_rank)} of ${tf.schedule_teams}), ${dog} ${num(td.schedule_strength)} (${ordinal(td.schedule_rank)}). Wins over above-average teams: ${fav} ${tf.quality_wins}, ${dog} ${td.quality_wins}. Schedule is already built into the ratings, so it adds no separate points.`
  const favPct = tf.wins / Math.max(1, tf.wins + tf.losses), dogPct = td.wins / Math.max(1, td.wins + td.losses)
  if (favPct < dogPct) schedule += ` ${fav} is favored despite the worse record (${record(tf)} vs ${record(td)}) because the models judge margins against opponent strength, not wins alone.`
  else if (tf.wins - td.wins >= 3 && o.total < 7) schedule += ` The records (${record(tf)} vs ${record(td)}) suggest a bigger gap than the forecast because the models count margins against opponent strength: close losses cost little and blowout wins count a lot.`

  // 3. Offense vs defense (Standard model's projected points).
  const st = g.standard
  const [favOff, dogOff] = favIsHome ? [st.home_offense_vs_away_defense, st.away_offense_vs_home_defense] : [st.away_offense_vs_home_defense, st.home_offense_vs_away_defense]
  const [favPts, dogPts] = favIsHome ? [st.home_points, st.away_points] : [st.away_points, st.home_points]
  const edge = favOff - dogOff
  const matchup = `Standard projects ${fav} ${Math.round(favPts)}, ${dog} ${Math.round(dogPts)}. ${fav}'s offense (${ordinal(tf.offense_rank)} in the Standard model) against ${dog}'s defense (${ordinal(td.defense_rank)}) is worth ${signed(favOff)} points against an average matchup; ${dog}'s offense (${ordinal(td.offense_rank)}) against ${fav}'s defense (${ordinal(tf.defense_rank)}) is worth ${signed(dogOff)}. ${Math.abs(edge) < 1 ? 'Neither side has a clear matchup edge.' : `That matchup edge favors ${edge > 0 ? fav : dog} by ${one(edge)} points before home field.`}`

  // 4. Recent performance (Momentum minus Standard, and last-three-game form).
  const shift = m.total - s.total
  const form = (name: string, t: ExplainedTeam) => t.recent_form == null || t.season_game_average == null ? null : `${name}'s last three games averaged ${signed(t.recent_form)} per game (opponent-adjusted), against ${signed(t.season_game_average)} across all its games`
  const forms = [form(fav, tf), form(dog, td)].filter(Boolean).join('; ')
  const recent = Math.abs(shift) < 0.5
    ? `Recent games tell the same story as the full season: Momentum, which counts recent games more, is within half a point of Standard.${forms ? ` ${forms}.` : ''}`
    : `Momentum, which counts recent games more, moves the forecast ${one(shift)} points toward ${shift > 0 ? fav : dog}.${forms ? ` ${forms}.` : ''}`

  // 5. Home field.
  const home = g.neutral_site ? 'Neutral site: no home-field points in any model.'
    : `${g.home} is at home, worth ${data.official_home_field.toFixed(1)} points in the official model and ${data.dual_home_field.toFixed(1)} in Standard and Momentum.`

  const factors: Factor[] = [
    { key: 'strength', title: 'Team strength (opponent-adjusted)', text: strength },
    { key: 'schedule', title: 'Schedule and quality of opponents', text: schedule },
    { key: 'matchup', title: 'Offense vs. defense', text: matchup },
    { key: 'recent', title: 'Recent performance', text: recent },
    { key: 'home', title: 'Home field', text: home },
  ]
  const models: ModelRow[] = [
    { model: 'Official', ...o }, { model: 'Standard', ...s }, { model: 'Momentum', ...m },
  ]
  const diffs = [Math.abs(o.total - s.total), Math.abs(s.total - m.total)]
  const modelDifference = Math.max(...diffs) < 1
    ? 'All three forecasts agree to within a point.'
    : [Math.abs(o.total - s.total) >= 1 ? `Official and Standard differ by ${one(o.total - s.total)} points: the official model rates teams from game margins and counts last season as ${data.official_prior_games} games; Standard rates offense and defense from points scored and counts it as ${data.dual_prior_games}.` : '',
       Math.abs(shift) >= 1 ? `Momentum differs from Standard by ${one(shift)} points because it counts recent games more.` : ''].filter(Boolean).join(' ')

  // Data-driven notes: only facts visible in the published inputs.
  const notes: string[] = []
  for (const [name, t] of [[g.home, th], [g.away, ta]] as const) {
    const w = t.weakest_game
    if (w && !w.opponent_fbs && w.points_for > w.points_against)
      notes.push(`${name}'s ${w.points_for}–${w.points_against} win over FCS ${w.opponent} counts as its weakest game (${signed(w.net_value)} against a ${signed(w.season_average)} season average): every FCS opponent is treated as one average FCS team, so even a comfortable win can rate below average.`)
  }
  return { favourite: fav, underdog: dog, headline, bottomLine: bottomLine(fav, dog, homeTeam, o), factors, models, modelDifference, notes, unavailable: data.unavailable }
}
