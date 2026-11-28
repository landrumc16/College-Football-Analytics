/** Optional rapid observations never replace the season report or archived forecasts. */
export type FastEvent = {
  game_id: string | number; home: string; away: string; home_score: number; away_score: number
  status: 'provisional' | 'confirmed' | 'corrected' | 'disputed'
  observed_at: string; verified_at?: string | null; statistics_pending: boolean
  source: string; basic_stats?: Record<string, unknown>; model_ingestion_allowed: boolean
}
export type FastResults = {
  schema_version: 1; generated_at: string; events: FastEvent[]
  records: Record<string, {wins: number; losses: number; provisional_games: number}>
  revision: number
}
const time = (v: unknown, now: number) => typeof v === 'string' && /(?:Z|[+-]\d\d:\d\d)$/.test(v) && Number.isFinite(Date.parse(v)) && Date.parse(v) <= now
const count = (v: unknown) => Number.isInteger(v) && Number(v) >= 0
export function parseFastResults(value: unknown, teams: readonly string[], now = Date.now()): FastResults | null {
  if (!value || typeof value !== 'object') return null
  const d = value as FastResults
  if (d.schema_version !== 1 || !time(d.generated_at, now) || !count(d.revision) || !Array.isArray(d.events) || !d.records || typeof d.records !== 'object' || Array.isArray(d.records)) return null
  const seen = new Set<string>()
  for (const e of d.events) {
    if (!e || !['string', 'number'].includes(typeof e.game_id) || !String(e.game_id).trim() || (typeof e.game_id === 'number' && (!Number.isInteger(e.game_id) || e.game_id < 0)) || seen.has(String(e.game_id)) || !teams.includes(e.home) || !teams.includes(e.away) || e.home === e.away || !count(e.home_score) || !count(e.away_score) || e.home_score === e.away_score || !['provisional', 'confirmed', 'corrected', 'disputed'].includes(e.status) || !time(e.observed_at, now) || typeof e.statistics_pending !== 'boolean' || typeof e.model_ingestion_allowed !== 'boolean') return null
    if (e.status === 'provisional') { if (e.model_ingestion_allowed) return null }
    else if (e.status !== 'disputed' || e.model_ingestion_allowed) { if (!time(e.verified_at, now)) return null }
    try { if (new URL(e.source).protocol !== 'https:') return null } catch { return null }
    seen.add(String(e.game_id))
  }
  for (const [team, r] of Object.entries(d.records)) {
    if (!teams.includes(team) || !r || !count(r.wins) || !count(r.losses) || !count(r.provisional_games)) return null
  }
  return d
}
