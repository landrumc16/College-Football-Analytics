/**
 * Market Analysis Calculator: pure, browser-local arithmetic.
 * Market numbers are typed by the user; nothing here fetches, stores or transmits them.
 * Team perspective: a spread is the selected team's line (negative = that team is favoured);
 * a model margin is the selected team's projected points minus the opponent's.
 */
export type Parsed = { ok: true; value: number } | { ok: false; error: string } | { ok: false; empty: true }
export type ModelView = { probability: number; margin: number }

const NUMBER = /^[+-]?(\d+(\.\d*)?|\.\d+)$/
const EPSILON = 1e-9

const clean = (raw: string) => raw.trim().replace(/−/g, '-').replace(/\s+/g, '')

export function parseSpread(raw: string): Parsed {
  const text = clean(raw)
  if (!text) return { ok: false, empty: true }
  if (/^(pk|pick|pickem|pick'em|even)$/i.test(text)) return { ok: true, value: 0 }
  if (!NUMBER.test(text)) return { ok: false, error: 'Enter a spread such as -7, +3.5 or PK.' }
  const value = Number(text)
  if (Math.abs(value) > 99.5) return { ok: false, error: 'A spread must be between -99.5 and +99.5 points.' }
  return { ok: true, value: value === 0 ? 0 : value }
}

export function parseProbability(raw: string): Parsed {
  const text = clean(raw).replace(/%$/, '')
  if (!text) return { ok: false, empty: true }
  if (!NUMBER.test(text) || text.startsWith('-') || text.startsWith('+')) return { ok: false, error: 'Enter a probability from 0 to 100, such as 62 or 62.5.' }
  const value = Number(text)
  if (value > 100) return { ok: false, error: 'A probability cannot be more than 100%.' }
  return { ok: true, value: value / 100 }
}

export function parseMoneyline(raw: string): Parsed {
  const text = clean(raw)
  if (!text) return { ok: false, empty: true }
  if (!NUMBER.test(text)) return { ok: false, error: 'Enter American odds such as -150 or +130.' }
  const value = Number(text)
  if (Math.abs(value) < 100) return { ok: false, error: 'American odds must be +100 or higher, or -100 or lower.' }
  if (Math.abs(value) > 100000) return { ok: false, error: 'American odds must be between -100000 and +100000.' }
  return { ok: true, value }
}

/** Raw implied probability; includes the bookmaker margin (vig), which is not removed. */
export function moneylineProbability(odds: number): number {
  if (!Number.isFinite(odds) || Math.abs(odds) < 100) throw new RangeError('invalid American odds')
  return odds > 0 ? 100 / (odds + 100) : -odds / (-odds + 100)
}

/** Selected team's view of a home-perspective model output. Never invents values. */
export function teamView(home: string, homeProbability: number, homeMargin: number, team: string): ModelView | null {
  if (!Number.isFinite(homeProbability) || homeProbability < 0 || homeProbability > 1 || !Number.isFinite(homeMargin)) return null
  return team === home ? { probability: homeProbability, margin: homeMargin } : { probability: 1 - homeProbability, margin: homeMargin === 0 ? 0 : -homeMargin }
}

/** Positive = the model is more favourable to the selected team than the entered spread. */
export const spreadDifference = (teamMargin: number, teamSpread: number) => teamMargin + teamSpread

/** Probability-point difference; positive = the model gives the selected team a higher chance. */
export const probabilityDifference = (model: number, market: number) => 100 * (model - market)

export const signed = (value: number, digits = 1) => {
  const rounded = Number(value.toFixed(digits))
  if (Math.abs(rounded) < EPSILON) return (0).toFixed(digits)
  return (rounded > 0 ? '+' : '') + rounded.toFixed(digits)
}
export const percent = (p: number, digits = 1) => (p * 100).toFixed(digits) + '%'
const points = (n: number) => `${Math.abs(n).toFixed(1)} point${Math.abs(Number(n.toFixed(1))) === 1 ? '' : 's'}`

export function describeMargin(team: string, margin: number): string {
  if (Math.abs(Number(margin.toFixed(1))) < EPSILON) return `Our model projects an even game for ${team}.`
  return margin > 0 ? `Our model projects ${team} to win by ${points(margin)}.` : `Our model projects ${team} to lose by ${points(margin)}.`
}

export function describeSpread(team: string, spread: number): string {
  if (spread === 0) return 'The entered spread is a pick\'em: neither team is favoured.'
  const size = `${Math.abs(spread).toFixed(1)}-point`
  return spread < 0 ? `The entered spread makes ${team} a ${size} favourite.` : `The entered spread makes ${team} a ${size} underdog.`
}

export function explainSpread(team: string, margin: number, spread: number): string {
  const d = Number(spreadDifference(margin, spread).toFixed(1))
  const gap = Math.abs(d) < EPSILON ? 'The model and the entered spread agree.'
    : d > 0 ? `The model is ${points(d)} more favourable to ${team} than the entered spread.`
    : `The model is ${points(d)} less favourable to ${team} than the entered spread.`
  return `${describeMargin(team, margin)} ${describeSpread(team, spread)} ${gap}`
}

export function explainProbability(team: string, model: number, market: number, source: 'prediction market' | 'moneyline'): string {
  const d = Number(probabilityDifference(model, market).toFixed(1))
  const what = source === 'moneyline' ? 'the raw probability implied by the entered moneyline' : 'the entered prediction-market probability'
  const gap = Math.abs(d) < EPSILON ? 'They match.'
    : `Our model is ${Math.abs(d).toFixed(1)} percentage points ${d > 0 ? 'higher' : 'lower'}.`
  return `Our model gives ${team} a ${percent(model)} chance to win; ${what} is ${percent(market)}. ${gap}`
}

/** When the selected team changes, express the same entered market from the other team's side. */
export function flipSpreadInput(raw: string): string {
  const parsed = parseSpread(raw)
  if (!parsed.ok) return raw
  return parsed.value === 0 ? '0' : signed(-parsed.value, Number.isInteger(parsed.value * 2) ? 1 : 2).replace(/\.0$/, '')
}

export function flipProbabilityInput(raw: string): string {
  const parsed = parseProbability(raw)
  if (!parsed.ok) return raw
  return String(Number((100 - parsed.value * 100).toFixed(2)))
}

/** Flip the sign of a typed spread or moneyline (phone decimal keypads often have no minus key). */
export function toggleSign(raw: string): string {
  const text = raw.trim().replace(/−/g, '-')
  if (!text) return '-'
  if (/^(pk|pick|pickem|pick'em|even|0+(\.0*)?)$/i.test(text)) return text
  if (text.startsWith('-')) return '+' + text.slice(1)
  if (text.startsWith('+')) return '-' + text.slice(1)
  return '-' + text
}

/** One-line result headline, read first; the full sentence follows. */
export function headlineSpread(team: string, margin: number, spread: number): string {
  const d = Number(spreadDifference(margin, spread).toFixed(1))
  if (Math.abs(d) < EPSILON) return `Model matches the spread for ${team}`
  return `Model is ${points(d)} ${d > 0 ? 'more' : 'less'} favourable to ${team}`
}

export function headlineProbability(team: string, model: number, market: number): string {
  const d = Number(probabilityDifference(model, market).toFixed(1))
  if (Math.abs(d) < EPSILON) return `Model matches the market for ${team}`
  return `Model gives ${team} ${Math.abs(d).toFixed(1)} percentage points ${d > 0 ? 'more' : 'less'} win chance`
}

export const spreadExample = (team: string) => `Example: ${team} −7 means ${team} is favored by 7; ${team} +3.5 means ${team} is a 3.5-point underdog.`

/** Spread sizes as written on a betting line: half points kept, whole numbers without ".0". */
const lineSize = (n: number) => { const v = Math.abs(n); return `${v % 1 ? v.toFixed(1) : v} point${v === 1 ? '' : 's'}` }
/** Compound form before a noun: "the 6.5-point spread". */
const spreadAdj = (n: number) => { const v = Math.abs(n); return `${v % 1 ? v.toFixed(1) : v}-point` }
/** Model margins rounded to the nearest half point for conversational text ("approximately 1 point"). */
const approxSize = (n: number) => lineSize(Math.round(Math.abs(n) * 2) / 2)

export type SpreadStory = { title: string; modelText: string; lineText: string; meaning: string; take: string }

/**
 * Four-part, plain-language comparison of the model's margin with a user-entered spread.
 * Inputs use the selected team's perspective (margin > 0 = team wins; spread < 0 = team favored), but the
 * story names teams explicitly, so it reads the same from either side. Calculations are unchanged.
 */
export function spreadStory(team: string, opponent: string, margin: number, spread: number): SpreadStory {
  const winner = Math.round(Math.abs(margin) * 2) / 2 < 0.5 ? null : margin > 0 ? team : opponent
  const favorite = spread === 0 ? null : spread < 0 ? team : opponent
  const other = (t: string) => t === team ? opponent : team
  const gap = Math.abs(spreadDifference(margin, spread))
  const much = gap >= 4 ? 'much ' : ''
  const modelText = winner ? `${winner} wins by approximately ${approxSize(margin)}.` : 'This looks like an even game: our model does not clearly favor either team.'
  const lineText = favorite ? `${favorite} is favored by ${lineSize(spread)}.` : 'Neither team is favored (pick’em).'
  const story = (title: string, meaning: string, take: string) => ({ title, modelText, lineText, meaning, take })
  if (!winner && !favorite) return story('Our model and the betting line agree',
    'Both our model and the betting line see this as an even game.',
    'There is no meaningful disagreement between our prediction and the line you entered.')
  if (gap < 1.5) return story('Our model and the betting line agree',
    winner && favorite && winner === favorite ? `Both our model and the betting line favor ${favorite} by a similar margin.` : 'Both our model and the betting line expect a close game.',
    'There is no major disagreement between our prediction and the line you entered.')
  if (winner && favorite && winner !== favorite) return story('Our model and the betting line disagree on the winner',
    `The betting line favors ${favorite}, but our model expects ${winner} to win.`,
    `This is a significant disagreement. Be cautious about ${favorite} covering the ${spreadAdj(spread)} spread. Our model expects ${winner} to win the game outright.`)
  if (!favorite) return story('Our model favors one team',
    `The betting line treats this game as a toss-up, but our model favors ${winner} by approximately ${approxSize(margin)}.`,
    `Our model leans toward ${winner} in a game the betting line treats as even.`)
  if (!winner) return story('Our model expects a closer game',
    `The betting line favors ${favorite}, but our model sees this as an even game.`,
    `Be cautious about ${favorite} covering the ${spreadAdj(spread)} spread. Our model expects ${other(favorite)} to keep this game competitive.`)
  if (Math.abs(margin) < Math.abs(spread)) return story('Our model expects a closer game',
    `Both our model and the betting line favor ${favorite}, but our model expects a ${much}closer game than the spread suggests.`,
    `Be cautious about ${favorite} covering the ${spreadAdj(spread)} spread. Our model expects ${other(favorite)} to keep this game competitive.`)
  return story('Our model expects a bigger win',
    `Both our model and the betting line favor ${favorite}, but our model expects a ${much}bigger win than the spread suggests.`,
    `Our model expects ${favorite} to win by more than the ${spreadAdj(spread)} spread. That difference is worth a closer look, not a guarantee of the result.`)
}
