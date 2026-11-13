/** Publication gate shared by historical program comparisons and Team Profiles.
 * The flag is an explicit source-review attestation, not proof by itself.
 * Refuse malformed or empty historical payloads even when that flag is set.
 */
export type HistoricalPayload = {
  schema_version?: unknown
  status?: unknown
  source_review_attested?: unknown
  predictive_validation?: unknown
  latest_completed_season?: unknown
  provenance_diagnostics?: unknown
  programs?: unknown
}

export function isPublishedHistoricalIntelligence(payload: unknown): payload is HistoricalPayload & { programs: unknown[] } {
  if (!payload || typeof payload !== 'object') return false
  const data = payload as HistoricalPayload
  if (data.schema_version !== 1 || data.status !== 'descriptive_only' ||
      data.source_review_attested !== true || data.predictive_validation !== false ||
      !Number.isInteger(data.latest_completed_season) || !Array.isArray(data.programs) ||
      data.programs.length === 0) return false

  const diagnostics = data.provenance_diagnostics
  if (!diagnostics || typeof diagnostics !== 'object') return false
  const coverage = diagnostics as Record<string, unknown>
  if (coverage.status !== 'provenance_format_checked_not_independently_verified' ||
      !Array.isArray(coverage.required_window) || coverage.required_window.length !== 2 ||
      coverage.required_window[1] !== data.latest_completed_season ||
      coverage.required_window[0] !== (data.latest_completed_season as number) - 9 ||
      !Number.isInteger(coverage.strength_programs_full_window) ||
      (coverage.strength_programs_full_window as number) < 1 ||
      !Number.isInteger(coverage.poll_programs_full_window) ||
      (coverage.poll_programs_full_window as number) < 1) return false

  const seen = new Set<string>()
  return data.programs.every(program => {
    if (!program || typeof program !== 'object') return false
    const row = program as Record<string, unknown>
    if (typeof row.team !== 'string' || !row.team.trim() || seen.has(row.team)) return false
    seen.add(row.team)
    return row.program_rankings !== undefined && row.hype !== undefined
  })
}
