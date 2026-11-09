/** Publication gate shared by historical program comparisons and Team Profiles.
 * A locally generated research payload is not evidence of source review.
 */
export type HistoricalPayload = {
  schema_version?: unknown
  status?: unknown
  source_review_attested?: unknown
  predictive_validation?: unknown
  programs?: unknown
}

export function isPublishedHistoricalIntelligence(payload: unknown): payload is HistoricalPayload & { programs: unknown[] } {
  if (!payload || typeof payload !== 'object') return false
  const data = payload as HistoricalPayload
  return data.schema_version === 1 &&
    data.status === 'descriptive_only' &&
    data.source_review_attested === true &&
    data.predictive_validation === false &&
    Array.isArray(data.programs)
}
