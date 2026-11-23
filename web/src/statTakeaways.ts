// Plain-English takeaways for statistical groups (unit-tested). Each one is derived from the displayed numbers only,
// uses cautious wording, and never states more certainty than the data supports. No team-specific text.

const one = (v: number) => Math.abs(v).toFixed(1)

/** Performance vs. expectations: wins minus the sum of archived pregame win probabilities. */
export function expectationTakeaway(team: string, aboveExpected: number, games: number): string {
  const size = Math.abs(aboveExpected)
  const side = aboveExpected > 0 ? 'ahead of' : 'behind'
  const verdict = size < 0.25 ? 'is right in line with expectations'
    : size < 1 ? `is slightly ${side} expectations`
    : size < 2 ? `is ${side} expectations`
    : `is well ${side} expectations`
  return `${team} ${verdict}${games < 5 ? `, though ${games} tracked ${games === 1 ? 'game is' : 'games are'} a small sample` : ''}.`
}

/** Season outlook: projected wins from the current record. */
export function outlookTakeaway(team: string, wins: number, projected: number): string {
  const more = projected - wins
  return more < 0.05 ? `${team} has finished its regular season with ${wins} wins.`
    : `${team} is projected for about ${projected.toFixed(1)} wins: ${wins} so far and roughly ${more.toFixed(1)} more from its remaining games.`
}

/** Team profile: model rank against the human polls. */
export function profileTakeaway(team: string, modelRank: number, ap: number | null | undefined, coaches: number | null | undefined, pollsAvailable: boolean): string {
  if (!pollsAvailable) return `${team} is No. ${modelRank} in our model.`
  const poll = ap ?? coaches
  const label = ap != null ? 'the AP poll' : 'the Coaches poll'
  if (poll == null) return modelRank <= 25 ? `Our model ranks ${team} No. ${modelRank} even though it is unranked in both polls.`
    : `${team} is unranked in both polls and No. ${modelRank} in our model.`
  const gap = modelRank - poll
  if (Math.abs(gap) < 5) return `Our model and the polls broadly agree on ${team} (model No. ${modelRank}, ${label} No. ${poll}).`
  return `Our model rates ${team} ${gap > 0 ? 'lower' : 'higher'} than ${label} does (model No. ${modelRank}, poll No. ${poll}).`
}

type RankRow = { team: string; rank: number; projected_wins: number; rating: number }
/** Model rankings: who leads and how tightly the top of the table is packed. */
export function rankingsTakeaway(rows: RankRow[]): string | null {
  const top = [...rows].sort((a, b) => a.rank - b.rank)
  if (top.length < 10) return null
  const ratingSpread = top[0].rating - top[9].rating
  return `${top[0].team} leads our rankings. The top 10 are separated by ${one(ratingSpread)} rating points: on a neutral field, No. 1 would be favored over No. 10 by about that many points.`
}

type PollRow = { team: string; rank: number }
/** AP vs Coaches: overlap and the biggest disagreement among teams ranked in both. */
export function pollTakeaway(ap: PollRow[], coaches: PollRow[]): string | null {
  if (!ap.length || !coaches.length) return null
  const c = new Map(coaches.map(r => [r.team, r.rank]))
  const shared = ap.filter(r => c.has(r.team))
  const split = shared.map(r => ({ team: r.team, ap: r.rank, coaches: c.get(r.team)!, gap: Math.abs(r.rank - c.get(r.team)!) }))
    .sort((a, b) => b.gap - a.gap || a.ap - b.ap)[0]
  const lead = `The AP and Coaches polls share ${shared.length} of their 25 teams`
  return split && split.gap >= 3 ? `${lead}; their biggest split is ${split.team} (AP No. ${split.ap}, Coaches No. ${split.coaches}).`
    : `${lead} and order them very similarly.`
}

type CfpRow = { team: string; cfp_field: number }
/** Playoff simulations: near-certain qualifiers and the closest bubble team. */
export function cfpTakeaway(rows: CfpRow[]): string | null {
  if (!rows.length) return null
  const locks = rows.filter(r => r.cfp_field >= 0.95).length
  const bubble = rows.filter(r => r.cfp_field > 0.2 && r.cfp_field < 0.8).sort((a, b) => Math.abs(a.cfp_field - 0.5) - Math.abs(b.cfp_field - 0.5))[0]
  const lead = `${locks} ${locks === 1 ? 'team makes' : 'teams make'} the field in at least 95% of simulated seasons`
  return bubble ? `${lead}; ${bubble.team} is closest to the bubble at ${Math.round(100 * bubble.cfp_field)}%.` : `${lead}.`
}

/** Verified pregame picks against a 50/50 coin flip on the same games (lower Brier is better). */
export function forecastTakeaway(games: number, brier: number, coinFlipBrier: number | undefined): string {
  if (coinFlipBrier == null) return `This is a small sample of ${games} verified predictions.`
  return brier < coinFlipBrier ? `In this small sample of ${games} games, the model's probabilities were more accurate than a coin flip.`
    : `In this small sample of ${games} games, the model's probabilities were not more accurate than a coin flip.`
}

type Graded = { label: string; score: number | null; grade: string | null }
/** Report Card: the strongest and weakest graded category (peer-relative 0-100 scores). */
export function reportCardTakeaway(team: string, categories: Graded[]): string | null {
  const graded = categories.filter(c => c.score != null && c.grade)
  if (graded.length < 2) return null
  const sorted = [...graded].sort((a, b) => b.score! - a.score!)
  const best = sorted[0], worst = sorted[sorted.length - 1]
  if (best.score! - worst.score! < 5) return `${team} grades about the same across its graded categories (${graded.map(c => `${c.label} ${c.grade}`).join(', ')}).`
  return `${team}'s strongest graded category is ${best.label} (${best.grade}); its weakest is ${worst.label} (${worst.grade}).`
}
