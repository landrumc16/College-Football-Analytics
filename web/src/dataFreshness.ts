// Per-area data freshness (unit-tested). Each area reports its own timestamp and an honest state instead of one
// global "last updated" time. Values come only from the published report and poll snapshot.

export type FreshnessState = 'current' | 'delayed' | 'awaiting' | 'unavailable'
export type FreshnessItem = { area: string; text: string; state: FreshnessState }
type Report = { retrieved_at?: string | null; generated_at?: string | null; data_freshness?: { retrieved_at?: string | null } }
type Polls = { poll_weeks?: Record<string, number>; ap_published_at?: string; coaches_published_at?: string
  cfp_published_at?: string; cfp_week?: number } | null

// Official 2026 CFP release dates (matches poll_refresh.CFP_DATES); releases are at 18:00 Central (selection day earlier).
export const CFP_RELEASES = ['2026-11-10', '2026-11-17', '2026-11-24', '2026-12-01', '2026-12-06']
const STALE_HOURS = 26          // the daily baseline refresh plus margin; event-driven runs are far more frequent

const day = (iso: string) => new Date(`${iso}T12:00:00Z`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' })
const when = (iso: string) => new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })

export function freshness(report: Report, polls: Polls, now: Date): FreshnessItem[] {
  const items: FreshnessItem[] = []
  const checked = report.data_freshness?.retrieved_at || report.retrieved_at
  if (!checked) items.push({ area: 'Scores and records', text: 'not published', state: 'unavailable' })
  else {
    const hours = (now.getTime() - new Date(checked).getTime()) / 36e5
    items.push({ area: 'Scores and records', text: `checked ${when(checked)}${hours > STALE_HOURS ? ' (update delayed)' : ''}`, state: hours > STALE_HOURS ? 'delayed' : 'current' })
  }
  items.push({ area: 'Model rankings and projections', text: report.generated_at ? `recalculated ${when(report.generated_at)}` : 'not published', state: report.generated_at ? 'current' : 'unavailable' })
  for (const [area, key, published] of [['AP Poll', 'ap_top25', polls?.ap_published_at], ['Coaches Poll', 'coaches_top25', polls?.coaches_published_at]] as const) {
    const week = polls?.poll_weeks?.[key]
    items.push(week ? { area, text: `week ${week}${published ? `, published ${day(published)}` : ''}`, state: 'current' }
      : { area, text: 'not yet published', state: 'unavailable' })
  }
  const verified = polls?.cfp_published_at
  // A release counts as due from 18:00 Central (00:00 UTC the next day) on its date.
  const due = CFP_RELEASES.filter(d => new Date(`${d}T00:00:00Z`).getTime() + 30 * 36e5 <= now.getTime()).pop()
  if (!verified) items.push({ area: 'CFP rankings', text: due ? `awaiting verification of the ${day(due)} release` : 'first release not yet due', state: due ? 'awaiting' : 'unavailable' })
  else if (due && due > verified) items.push({ area: 'CFP rankings', text: `${day(verified)} release shown; ${day(due)} release awaiting verification`, state: 'awaiting' })
  else items.push({ area: 'CFP rankings', text: `${day(verified)} release (verified)`, state: 'current' })
  return items
}

/** One-line summary: "all current", or the areas that are delayed, awaiting verification or unavailable. */
export function statusSummary(items: FreshnessItem[]): string {
  const label: Record<FreshnessState, string> = { current: '', delayed: 'update delayed', awaiting: 'awaiting verification', unavailable: 'unavailable' }
  const flagged = items.filter(i => i.state !== 'current').map(i => `${i.area} ${label[i.state]}`)
  return flagged.length ? flagged.join('; ') : 'all current'
}
