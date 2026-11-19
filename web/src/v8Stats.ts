// V8 Offense & Defense data helpers (pure; unit-tested). Values come only from v8-team-stats.json.

export type MetricRow = (number | null)[] // [raw, raw_rank, power, power_rank, power_games, adjusted, se, adjusted_rank, n]
export type Trend = { recent: number; season: number; change: number; se: number | null; label: 'improving' | 'declining' | 'steady'; games: number } | null
export type TeamStats = {
  conference: string | null; power: boolean; games: number; fcs_games: number; power_games: number; games_with_play_data: number
  ppg: number | null; papg: number | null
  offense: Record<string, MetricRow>; defense: Record<string, MetricRow>
  trend: Record<string, Trend>; volatility: Record<string, { sd: number; games: number } | null>
}
export type Definition = { label: string; numerator: string; denominator: string; offense_higher_is_better: boolean; prior: number; group: string }
export type V8Stats = {
  season: number; as_of: string | null; generated_at: string; source: string; fields: string[]
  definitions: Record<string, Definition>; league: Record<string, { mean: number; home: number }>
  power_conferences: string[]; fbs_teams: number; power_teams: number
  coverage: { completed_games: number; games_with_plays: number } | null
  method: Record<string, string>; teams: Record<string, TeamStats>
}
export type View = 'raw' | 'power' | 'adjusted'
export type Side = 'offense' | 'defense'

export const GROUPS: { id: string; label: string; metrics: string[] }[] = [
  { id: 'scoring', label: 'Scoring and efficiency', metrics: ['ppd', 'epa', 'sr', 'ypp', 'expl'] },
  { id: 'rushing', label: 'Running game', metrics: ['rush_sr', 'rush_ypc', 'rush_expl', 'stuff'] },
  { id: 'passing', label: 'Passing game', metrics: ['pass_sr', 'pass_ypd', 'pass_expl', 'sack'] },
  { id: 'situational', label: 'Situational', metrics: ['third', 'rz_td', 'rz_pts', 'late', 'to'] },
]
const RATE = new Set(['sr', 'expl', 'rush_sr', 'rush_expl', 'stuff', 'pass_sr', 'pass_expl', 'sack', 'third', 'rz_td', 'late'])
const UNIT: Record<string, string> = { ppd: 'drives', rz_pts: 'trips', rz_td: 'trips', to: 'drives', third: 'third downs', late: 'plays',
  rush_sr: 'runs', rush_ypc: 'runs', rush_expl: 'runs', stuff: 'runs', pass_sr: 'dropbacks', pass_ypd: 'dropbacks', pass_expl: 'dropbacks', sack: 'dropbacks' }

export const field = (row: MetricRow | undefined, view: View) => {
  if (!row) return { value: null, rank: null, se: null, games: null }
  if (view === 'raw') return { value: row[0], rank: row[1], se: null, games: null }
  if (view === 'power') return { value: row[2], rank: row[3], se: null, games: row[4] }
  return { value: row[5], rank: row[7], se: row[6], games: null }
}

export function format(metric: string, value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return 'N/A'
  if (RATE.has(metric)) return `${(100 * value).toFixed(1)}%`
  if (metric === 'epa' || metric === 'to') return value.toFixed(2)
  return value.toFixed(metric === 'ppd' || metric === 'rz_pts' ? 2 : 1)
}

export const sampleUnit = (metric: string) => UNIT[metric] ?? 'plays'

/** Lower values are better for this side and metric (e.g. points allowed per drive, offensive sack rate). */
export function lowerIsBetter(defs: Record<string, Definition>, metric: string, side: Side) {
  const higherOffense = defs[metric]?.offense_higher_is_better ?? true
  return side === 'offense' ? !higherOffense : higherOffense
}

/** Pool size for a view: all FBS teams, or power teams for the power-opponent view. */
export const poolSize = (data: V8Stats, view: View) => (view === 'power' ? data.power_teams : data.fbs_teams)

export function leaderboard(data: V8Stats, metric: string, side: Side, view: View) {
  return Object.entries(data.teams)
    .map(([team, t]) => ({ team, conference: t.conference, ...field(t[side][metric], view) }))
    .filter(row => row.rank != null && row.value != null)
    .sort((a, b) => (a.rank! - b.rank!) || a.team.localeCompare(b.team))
}

/** Expected value of `offense` team's unit against `defense` team's unit on a neutral field (additive model). */
export function expected(data: V8Stats, metric: string, offense: string, defense: string): number | null {
  const o = data.teams[offense]?.offense[metric]?.[5], d = data.teams[defense]?.defense[metric]?.[5], mean = data.league[metric]?.mean
  if (o == null || d == null || mean == null) return null
  return o + d - mean
}

function spread(data: V8Stats, metric: string, side: Side) {
  const values = Object.values(data.teams).map(t => t[side][metric]?.[5]).filter((v): v is number => v != null)
  const m = values.reduce((s, v) => s + v, 0) / values.length
  return Math.sqrt(values.reduce((s, v) => s + (v - m) ** 2, 0) / values.length) || 1
}

export type Edge = { metric: string; label: string; offense: string; defense: string; expected: number; mean: number; size: number; favours: string; offenseValue: number; defenseValue: number }

/** Phase-by-phase edges for both units in a matchup, sized in national standard deviations (positive favours the offense). */
export function matchupEdges(data: V8Stats, a: string, b: string, metrics = ['epa', 'rush_sr', 'pass_sr', 'expl', 'pass_expl', 'rush_expl', 'sack', 'third', 'rz_td', 'ppd']): Edge[] {
  const edges: Edge[] = []
  for (const [offense, defense] of [[a, b], [b, a]]) {
    for (const metric of metrics) {
      const value = expected(data, metric, offense, defense), mean = data.league[metric]?.mean
      if (value == null || mean == null) continue
      const sign = data.definitions[metric].offense_higher_is_better ? 1 : -1
      const size = sign * (value - mean) / spread(data, metric, 'offense')
      edges.push({ metric, label: data.definitions[metric].label, offense, defense, expected: value, mean, size,
        favours: size >= 0 ? offense : defense,
        offenseValue: data.teams[offense].offense[metric][5] as number, defenseValue: data.teams[defense].defense[metric][5] as number })
    }
  }
  return edges
}

/** The largest edges in plain language (only |size| >= 0.5 national SD counts as notable). */
export function notableEdges(edges: Edge[], limit = 4) {
  return edges.filter(e => Math.abs(e.size) >= 0.5).sort((x, y) => Math.abs(y.size) - Math.abs(x.size)).slice(0, limit)
}

export function describeEdge(e: Edge): string {
  const strength = Math.abs(e.size) >= 1 ? 'clear' : 'modest'
  const who = e.size >= 0 ? `${e.offense}'s offense` : `${e.defense}'s defense`
  return `${strength[0].toUpperCase() + strength.slice(1)} edge for ${who}: ${e.label.toLowerCase()} expected at ${format(e.metric, e.expected)} vs the national average of ${format(e.metric, e.mean)}.`
}

/** Plain-English explanation built only from the two units' adjusted values and the national average. */
export function explainEdge(e: Edge): string {
  const measure = e.label.charAt(0).toLowerCase() + e.label.slice(1)
  return `Against average opponents, ${e.offense}'s offense posts ${format(e.metric, e.offenseValue)} and ${e.defense}'s defense allows ${format(e.metric, e.defenseValue)} (${measure}). Together that points to about ${format(e.metric, e.expected)}, against a national average of ${format(e.metric, e.mean)}.`
}

export const edgeStrength = (e: Edge) => (Math.abs(e.size) >= 1 ? 'Clear edge' : 'Modest edge')

/** Card heading: the team that benefits and which unit, e.g. "Texas Tech defensive advantage". */
export const advantageLabel = (e: Edge) => `${e.favours} ${e.size >= 0 ? 'offensive' : 'defensive'} advantage`

/** One short sentence: which unit is expected to beat the national average, on which measure. */
export function shortReason(e: Edge): string {
  const measure = e.label.charAt(0).toLowerCase() + e.label.slice(1)
  return e.size >= 0
    ? `${e.offense}'s offense is expected to beat the national average on ${measure} against ${e.defense}.`
    : `${e.defense}'s defense is expected to beat the national average on ${measure} against ${e.offense}.`
}

export function percentile(rank: number | null, pool: number) {
  return rank == null || pool < 2 ? null : Math.round(100 * (pool - rank) / (pool - 1))
}
