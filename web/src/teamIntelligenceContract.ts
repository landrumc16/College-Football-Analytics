/** V9 offline artifact contract. UI integration follows in Milestone 2. */
export type SourceAge = {
  status: 'missing' | 'invalid' | 'future' | 'stale' | 'current'
  age_hours: number | null
}
export type IntelligenceMetric<T = number> = {
  value: T | null
  units: string
  population: string
  sample: number | null
  source: string
  source_receipt: string | null
  period: { season: number; through: string | null }
  freshness: SourceAge
  limitations: string[]
  status: 'available' | 'unavailable'
}
export type IntelligenceFinding = {
  id: string
  rule_version: number
  takeaway: string
  evidence_paths: string[]
  source_receipt: string | null
  explanation: string
}
