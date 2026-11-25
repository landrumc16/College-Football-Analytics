// Per-area data freshness (unit-tested). Each area reports its own timestamp and an honest state instead of one
// global "last updated" time. Values come from the published report and poll snapshot, plus the deployed
// monitor-status.json (event watcher state and the automatic freshness monitor's open alerts).

export type FreshnessState = 'current' | 'delayed' | 'awaiting' | 'unavailable'
export type FreshnessItem = { area: string; text: string; state: FreshnessState }
type Report = { retrieved_at?: string | null; generated_at?: string | null; data_freshness?: { retrieved_at?: string | null }
  summary?: { upcoming_games?: number } }
type Polls = { poll_weeks?: Record<string, number>; ap_published_at?: string; coaches_published_at?: string
  cfp_published_at?: string; cfp_week?: number } | null
export type MonitorAlert = { key?: string; area: string; severity: 'critical' | 'warning'; text: string }
// monitor-status.json, written at each deployment and whenever the monitor's alerts change.
export type MonitorStatus = { generated_at?: string; watcher?: { state?: 'active' | 'stopped' | 'idle' | 'unknown'; last_run_at?: string | null }
  alerts: MonitorAlert[] }

// Official 2026 CFP release dates (matches poll_refresh.CFP_DATES). Weekly releases air at 18:00 Central (00:00 UTC
// the next day); selection day (Sunday 6 December) at 11:00 Central (17:00 UTC).
export const CFP_RELEASES = ['2026-11-10', '2026-11-17', '2026-11-24', '2026-12-01', '2026-12-06']
const CFP_GRACE_MINUTES = 15    // publication target is five minutes; flag a release still missing after 15
const STALE_HOURS = 26          // the daily baseline refresh plus margin; event-driven runs are far more frequent

const day = (iso: string) => new Date(`${iso}T12:00:00Z`).toLocaleDateString(undefined, { month: 'short', day: 'numeric', timeZone: 'UTC' })
const when = (iso: string) => new Date(iso).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })

/** When a CFP release counts as overdue if it is still not published (release time + grace). */
export function cfpOverdueAt(release: string): number {
  const d = new Date(`${release}T00:00:00Z`)
  const sunday = d.getUTCDay() === 0
  return d.getTime() + (sunday ? 17 * 36e5 : 24 * 36e5) + CFP_GRACE_MINUTES * 6e4
}

/** Live monitoring state from the deployed monitor status, or null when it is unknown. */
export function monitoringItem(status: MonitorStatus | undefined): FreshnessItem | null {
  if (!status) return null
  const stopped = status.alerts.some(a => a.key === 'watcher-stopped' && a.severity === 'critical')
  if (stopped || status.watcher?.state === 'stopped') {
    const since = status.watcher?.last_run_at ? ` since ${when(status.watcher.last_run_at)}` : ''
    return { area: 'Live monitoring', text: `interrupted${since}; automatic updates may be delayed`, state: 'delayed' }
  }
  if (status.watcher?.state === 'active') return { area: 'Live monitoring', text: 'active', state: 'current' }
  if (status.watcher?.state === 'idle') return { area: 'Live monitoring', text: 'idle (no games left to watch)', state: 'current' }
  return null
}

export function freshness(report: Report, polls: Polls, now: Date, status?: MonitorStatus): FreshnessItem[] {
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
  const due = CFP_RELEASES.filter(d => cfpOverdueAt(d) <= now.getTime()).pop()
  if (!verified) items.push({ area: 'CFP rankings', text: due ? `awaiting verification of the ${day(due)} release` : 'first release not yet due', state: due ? 'awaiting' : 'unavailable' })
  else if (due && due > verified) items.push({ area: 'CFP rankings', text: `${day(verified)} release shown; ${day(due)} release awaiting verification`, state: 'awaiting' })
  else items.push({ area: 'CFP rankings', text: `${day(verified)} release (verified)`, state: 'current' })
  // Problems the automatic monitor has found (critical only): they override the area's own state.
  for (const alert of status?.alerts.filter(a => a.severity === 'critical' && a.key !== 'watcher-stopped') ?? []) {
    const item = items.find(i => i.area === alert.area)
    if (item) { item.text = alert.text; item.state = 'delayed' }
    else items.push({ area: alert.area, text: alert.text, state: 'delayed' })
  }
  const monitoring = monitoringItem(status)
  if (monitoring) items.push(monitoring)
  return items
}

/** One-line summary: "all current", or the areas that are delayed, awaiting verification or unavailable. */
export function statusSummary(items: FreshnessItem[]): string {
  const label: Record<FreshnessState, string> = { current: '', delayed: 'update delayed', awaiting: 'awaiting verification', unavailable: 'unavailable' }
  const flagged = items.filter(i => i.state !== 'current').map(i => i.area === 'Live monitoring' ? 'Live monitoring interrupted' : `${i.area} ${label[i.state]}`)
  return flagged.length ? flagged.join('; ') : 'all current'
}
