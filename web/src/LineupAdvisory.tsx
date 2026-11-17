/** A verified lineup-change advisory is context, never a score adjustment. */
export type LineupChangeAdvisory = {
  team: string
  position: string
  change: 'replacement' | 'injury' | 'return'
  effective_at: string
  verified_at: string
  source_url: string
  games_with_new_lineup: number
  current_lineup_confirmed: boolean
}
const timestamp = (s: string) => /(?:Z|[+-]\d\d:\d\d)$/.test(s) ? Date.parse(s) : NaN
export function validLineupAdvisory(value: unknown, team: string, asOf: string, window = 3): value is LineupChangeAdvisory {
  if (!value || typeof value !== 'object' || !Number.isInteger(window) || window < 1) return false
  const a = value as Partial<LineupChangeAdvisory>
  const now = timestamp(asOf)
  const effective = timestamp(a.effective_at ?? '')
  const verified = timestamp(a.verified_at ?? '')
  if (![now, effective, verified].every(Number.isFinite) || effective > now || verified > now) return false
  if (a.team !== team || !a.position?.trim() ||
      !['replacement', 'injury', 'return'].includes(a.change ?? '') ||
      a.current_lineup_confirmed !== true ||
      !Number.isInteger(a.games_with_new_lineup) ||
      (a.games_with_new_lineup ?? -1) < 0 ||
      (a.games_with_new_lineup ?? window) >= window) return false
  try {
    const url = new URL(a.source_url ?? '')
    return url.protocol === 'https:' && Boolean(url.hostname)
  } catch { return false }
}
export function LineupAdvisoryNotice({ advisory, team, asOf }: {
  advisory: unknown; team: string; asOf: string
}) {
  if (!validLineupAdvisory(advisory, team, asOf)) return null
  return <aside role="note" aria-label="Lineup change prediction advisory" className="notice lineup-change-advisory">
    <strong>Lineup change — prediction uncertainty elevated</strong>
    <p>A verified change at {advisory.position} means this forecast may be less reliable
      until more games show how the current lineup performs. This notice does not
      automatically change the projected score.</p>
    <p>{advisory.games_with_new_lineup} of 3 provisional observation games completed.{' '}
      <a href={advisory.source_url} target="_blank" rel="noopener noreferrer">Verified source</a>
    </p>
  </aside>
}
