/** Optional rapid observations never replace the season report or archived forecasts. */
export type FastEvent = {
  game_id: string | number; home: string; away: string; home_score: number; away_score: number
  status: 'provisional' | 'confirmed' | 'corrected' | 'disputed'
  observed_at: string; verified_at?: string | null; statistics_pending: boolean
  source: string; statistics_verified?: boolean; statistics_source?: string; basic_stats?: Record<string, unknown>; model_ingestion_allowed: boolean
}
export type FastResults = {
  schema_version: 1; generated_at: string; events: FastEvent[]
  records: Record<string, {wins: number; losses: number; provisional_games: number}>
  revision: number
}
const time = (v: unknown, now: number) => typeof v === 'string' && /(?:Z|[+-]\d\d:\d\d)$/.test(v) && Date.parse(v) <= now
const count = (v: unknown) => Number.isInteger(v) && Number(v) >= 0
export type FastScheduleGame = {game_id: string | number; home: string; away: string}
export function parseFastResults(value: unknown, schedule: readonly FastScheduleGame[], now = Date.now()): FastResults | null {
  if (!value || typeof value !== 'object') return null
  const d = value as FastResults
  if (d.schema_version !== 1 || !time(d.generated_at, now) || !count(d.revision) || !Array.isArray(d.events) || !d.records || typeof d.records !== 'object' || Array.isArray(d.records)) return null
  const games = new Map(schedule.map(game => [String(game.game_id), game]))
  const seen = new Set<string>()
  for (const e of d.events) {
    const scheduled = e && games.get(String(e.game_id))
    if (!e || seen.has(String(e.game_id)) || !scheduled || scheduled.home !== e.home || scheduled.away !== e.away || !count(e.home_score) || !count(e.away_score) || e.home_score === e.away_score || !['provisional', 'confirmed', 'corrected', 'disputed'].includes(e.status) || !time(e.observed_at, now) || typeof e.statistics_pending !== 'boolean' || typeof e.model_ingestion_allowed !== 'boolean') return null
    if (e.status === 'provisional') { if (e.model_ingestion_allowed) return null }
    else if (e.status !== 'disputed' || e.model_ingestion_allowed) { if (!time(e.verified_at, now)) return null }
    try { if (new URL(e.source).protocol !== 'https:') return null } catch { return null }
    seen.add(String(e.game_id))
  }
  for (const r of Object.values(d.records)) {
    if (!r || ![r.wins, r.losses, r.provisional_games].every(count)) return null
  }
  return d
}
