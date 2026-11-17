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

export const spreadExample = (team: string) => `Example: ${team} −7 means ${team} is favoured by 7; ${team} +3.5 means ${team} is a 3.5-point underdog.`

/** Plain-language spread comparison; keeps the signed arithmetic unchanged. */
export function spreadStory(team: string, opponent: string, margin: number, spread: number) {
  const modelWinner = Math.abs(margin) < 0.05 ? null : margin > 0 ? team : opponent
  const lineFavorite = Math.abs(spread) < 0.05 ? null : spread < 0 ? team : opponent
  const modelSize = Math.abs(margin)
  const lineSize = Math.abs(spread)
  const modelText = modelWinner ? `Our model predicts ${modelWinner} will win by approximately ${points(modelSize)}.` : 'Our model predicts an even game.'
  const lineText = lineFavorite ? `The betting line you entered has ${lineFavorite} favored by ${points(lineSize)}.` : 'The betting line you entered has neither team favored (pick’em).'
  const gap = Math.abs(margin + spread)
  if (gap < 1.5) return {
    title: 'Our model and the spread are close',
    modelText, lineText,
    meaning: 'Our model and the entered betting line tell a similar story about this matchup.',
    take: 'There is no major disagreement between our prediction and the spread you entered.',
  }
  if (modelWinner && lineFavorite && modelWinner !== lineFavorite) return {
    title: 'Our model and the spread disagree',
    modelText, lineText,
    meaning: 'Our model predicts a different winner from the team favored by the entered betting line.',
    take: 'This is a significant disagreement. Look more closely at the matchup before drawing conclusions from the spread.',
  }
  const closer = modelSize < lineSize
  const qualifier = gap >= 4 ? 'much ' : ''
  const meaning = closer
    ? `Both point toward ${lineFavorite ?? modelWinner}, but our model expects a ${qualifier}closer game than the spread suggests.`
    : `Both point toward ${modelWinner ?? lineFavorite}, but our model expects a ${qualifier}bigger win than the spread suggests.`
  return {
    title: closer ? 'Our model expects a closer game' : 'Our model expects a bigger win',
    modelText, lineText, meaning,
    take: closer && lineFavorite
      ? `Be cautious about ${lineFavorite} covering this spread. Our model expects ${lineFavorite === team ? opponent : team} to keep the game more competitive.`
      : 'Our model expects a larger winning margin than the entered spread suggests. That difference is worth examining, not a guarantee of a result.',
  }
}
