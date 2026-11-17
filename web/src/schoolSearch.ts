/** Shared school matching for every school picker: exact, then prefix, then word-prefix, then partial matches. */
// Widely used abbreviations; an entry only applies when its school is in the list being searched.
export const SCHOOL_ALIASES: Record<string, string[]> = {
  TTU: ['Texas Tech'], UGA: ['Georgia'], OU: ['Oklahoma'], OSU: ['Ohio State', 'Oklahoma State', 'Oregon State'],
  FSU: ['Florida State'], UNC: ['North Carolina'], UVA: ['Virginia'], VT: ['Virginia Tech'], ND: ['Notre Dame'],
  ASU: ['Arizona State'], BC: ['Boston College'], KSU: ['Kansas State'], ISU: ['Iowa State'], WVU: ['West Virginia'],
  UF: ['Florida'], PSU: ['Penn State'], MSU: ['Michigan State', 'Mississippi State'], UK: ['Kentucky'], USF: ['South Florida'],
  FAU: ['Florida Atlantic'], FIU: ['Florida International'], UMASS: ['Massachusetts'], JMU: ['James Madison'],
  WKU: ['Western Kentucky'], NIU: ['Northern Illinois'], MTSU: ['Middle Tennessee'], BGSU: ['Bowling Green'],
  TAMU: ['Texas A&M'], 'OLE MISS': ['Ole Miss'], MIAMI: ['Miami (FL)', 'Miami (OH)'],
}
export const MAX_SUGGESTIONS = 8

/** Lower-case, accents removed, punctuation collapsed: "San José State" -> "san jose state". */
export const normalize = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9&]+/g, ' ').trim()

export function rankSchools(query: string, schools: string[], limit = MAX_SUGGESTIONS): string[] {
  const q = normalize(query)
  if (!q) return []
  const alias = new Set((SCHOOL_ALIASES[q.toUpperCase()] || []).filter(s => schools.includes(s)))
  const scored: [number, string][] = []
  for (const school of schools) {
    const n = normalize(school)
    const tier = n === q ? 0 : alias.has(school) ? 1 : n.startsWith(q) ? 2 : n.split(' ').some(w => w.startsWith(q)) ? 3 : n.includes(q) ? 4 : -1
    if (tier >= 0) scored.push([tier, school])
  }
  return scored.sort((a, b) => a[0] - b[0] || a[1].localeCompare(b[1])).slice(0, limit).map(([, s]) => s)
}

/** The school whose name equals the query (case/accent-insensitive), if any. */
export const exactSchool = (query: string, schools: string[]) => schools.find(s => normalize(s) === normalize(query)) ?? null
