// Automatic monitoring status for the "Data status" footer. The deployment writes monitor-status.json next to the app
// (watcher state and the freshness monitor's open alerts), and the monitor redeploys whenever its alerts change, so
// the site never contacts a third party for it. Any failure leaves the status unknown rather than claiming coverage.
import type { MonitorStatus } from './dataFreshness'

export async function loadMonitorStatus(): Promise<MonitorStatus | undefined> {
  try {
    const r = await fetch(import.meta.env.BASE_URL + 'monitor-status.json', { cache: 'no-store' })
    if (!r.ok || !r.headers.get('content-type')?.includes('json')) return undefined
    const data = await r.json() as MonitorStatus
    return data && typeof data === 'object' && Array.isArray(data.alerts) ? data : undefined
  } catch { return undefined }
}
