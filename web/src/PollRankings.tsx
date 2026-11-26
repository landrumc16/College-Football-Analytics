import { titleCase } from './titleCase'
type PollEntry = { team: string; rank: number }
import { StatExplain, Takeaway } from './StatExplain'
import { pollTakeaway } from './statTakeaways'
type Snapshot = { season: number; week: number; source: string; ap_top25: PollEntry[]; coaches_top25: PollEntry[] }
export type PollSortKey = 'ap' | 'coaches'

// Poll feeds use CFBD school names; match them to the app's canonical names (same verified aliases as the pipeline).
const ALIASES: Record<string, string> = { Miami: 'Miami (FL)', 'App State': 'Appalachian State', 'Sam Houston': 'Sam Houston State', 'UL Monroe': 'ULM' }
const canonical = (team: string) => ALIASES[team] ?? team
const LABELS: Record<PollSortKey, string> = { ap: 'AP', coaches: 'Coaches' }

export default function PollRankings({ snapshot, conferenceTeams, search, onSearch, conference, onConference, sort, onSort }: {
  snapshot: Snapshot; conferenceTeams: Record<string, string[]>; search: string; onSearch: (value: string) => void
  conference: string; onConference: (value: string) => void; sort: PollSortKey; onSort: (value: PollSortKey) => void
}) {
  const rows = new Map<string, { team: string; ap: number | null; coaches: number | null }>()
  for (const key of ['ap', 'coaches'] as const) {
    for (const entry of key === 'ap' ? snapshot.ap_top25 : snapshot.coaches_top25) {
      const team = canonical(entry.team)
      const row = rows.get(team) ?? { team, ap: null, coaches: null }
      row[key] = entry.rank
      rows.set(team, row)
    }
  }
  const tied = (key: PollSortKey, rank: number | null) =>
    rank != null && (key === 'ap' ? snapshot.ap_top25 : snapshot.coaches_top25).filter(e => e.rank === rank).length > 1
  const display = (key: PollSortKey, rank: number | null) => rank == null ? 'NR' : `${tied(key, rank) ? 'T-' : ''}${rank}`
  const spoken = (key: PollSortKey, rank: number | null) => rank == null ? 'not ranked' : `${tied(key, rank) ? 'tied ' : ''}${rank}`
  const other: PollSortKey = sort === 'ap' ? 'coaches' : 'ap'
  const members = conference === 'all' ? null : new Set(conferenceTeams[conference] || [])
  const query = search.trim().toLowerCase()
  const visible = [...rows.values()]
    .filter(row => !query || row.team.toLowerCase().includes(query))
    .filter(row => !members || members.has(row.team))
    // Ranked teams first by the selected poll (ties share a rank), then the other poll, then name; NR last.
    .sort((a, b) => (a[sort] ?? Infinity) - (b[sort] ?? Infinity) || (a[other] ?? Infinity) - (b[other] ?? Infinity) || a.team.localeCompare(b.team))
  const header = (key: PollSortKey) => (
    <th scope="col" aria-sort={sort === key ? 'ascending' : 'none'}>
      <button type="button" className="poll-sort-button" onClick={() => onSort(key)} aria-label={`Sort by ${LABELS[key]} Poll ranking`}>
        {titleCase(LABELS[key])}<span aria-hidden="true">{sort === key ? ' ▲' : ''}</span>
      </button>
    </th>
  )
  return <section className="notice poll-rankings">
    <h2>Poll Rankings</h2>
    <p>AP and Coaches Top 25 side by side. NR means the school is not ranked in that poll. These are the published polls, not predictions.</p>
    <p>Poll season {snapshot.season} · Week {snapshot.week} · Source: {snapshot.source}.</p>
    {pollTakeaway(snapshot.ap_top25, snapshot.coaches_top25) && <Takeaway>{pollTakeaway(snapshot.ap_top25, snapshot.coaches_top25)}</Takeaway>}
    <div className="poll-filters">
      <label>Search Teams <input aria-label="Search poll teams" placeholder="Search teams…" value={search} onChange={e => onSearch(e.target.value)} /></label>
      <label>Conference <select aria-label="Filter polls by conference" value={conference} onChange={e => onConference(e.target.value)}>
        <option value="all">All Conferences</option>
        {Object.keys(conferenceTeams).sort().map(name => <option key={name} value={name}>{name}</option>)}
      </select></label>
    </div>
    <p className="visually-hidden" role="status" aria-live="polite">Sorted by {LABELS[sort]} Poll ranking</p>
    <div className="table-wrap poll-rankings-table">
      <table>
        <caption className="visually-hidden">AP and Coaches Poll Rankings, Sorted by {LABELS[sort]} Poll</caption>
        <thead><tr><th scope="col">Team</th>{header('ap')}{header('coaches')}</tr></thead>
        <tbody>{visible.map(row => <tr key={row.team}>
          <th scope="row" className="team">{row.team}</th>
          <td aria-label={`AP ${spoken('ap', row.ap)}`}>{display('ap', row.ap)}</td>
          <td aria-label={`Coaches ${spoken('coaches', row.coaches)}`}>{display('coaches', row.coaches)}</td>
        </tr>)}</tbody>
      </table>
      {!visible.length && <p role="status">No ranked teams match this search or conference.</p>}
    </div>
    <small>Tap AP or Coaches to sort by that poll. Tied ranks are shown as T-n and keep their published rank. Teams ranked in only one poll show NR in the other.</small>
    <StatExplain><p>The <strong>AP Top 25</strong> is voted on by sports journalists and the <strong>Coaches Poll</strong> by head coaches, each released weekly during the season. They reflect voters' judgment of the best teams, not a statistical model, so they can differ from each other and from our model rankings.</p><p>A team's poll rank can lag its results by a week, and voters weigh records, recent games and reputation differently. Use the polls to see how teams are perceived; use Model Rankings for the model's own estimate.</p></StatExplain>
  </section>
}
