# Sustainable acquisition — November 27, 2026

Issue #74 remains open. No new provider request, subscription or entitlement probe was used for this assessment. Access without documented automation permission is not an adopted source. Unknown limits below are unresolved, not unlimited.

| Source | Coverage | Permission / cost | Cadence, limits and decision |
| --- | --- | --- | --- |
| CFBD existing API | Schedules, results, team/player stats, derived advanced stats, AP/Coaches/CFP | Existing key; commercial app use permitted under API terms; raw redistribution restricted | 1,000 monthly free; shared with basketball; no public first-availability SLA established. Existing batched acquisition remains primary. |
| CFBD Tier 1 | Existing data plus live scoreboard | Published $1/month, 5,000 calls; no purchase made | Minimum published paid option identified for assumed peak demand; entitlement and real latency still require validation after owner action. |
| CFBD academic | Core data | 3,000 free with eligible educational email | Owner eligibility unknown; cannot assume available. |
| NCAA.org / NCAA.com | Results, schedules, stats | NCAA.org terms prohibit unauthorized automated collection; NCAA.com separately operated terms | No authorized rapid API established. Public access is not permission. Not adopted. |
| University athletics / conference sites | Own-team/conference schedules, kickoff changes, box scores, selections | Site-specific publisher/vendor permission required; no blanket national grant found | Fragmented coverage, unknown automation limits and release guarantees. Big12 communications and Texas Tech publications useful provenance, not an authorized national feed. Retail shop terms do not govern athletics pages. |
| StatBroadcast | University live status, scores and detailed stats | Terms require prior express written consent for systematic extraction and third-party retrieval | Public display delay documented at 5–10 seconds, but this does not grant collection rights. Not adopted. |
| AP | Authoritative AP Top 25 | Licensed sports/API products; account-specific quote and quotas | API exposes account quotas; no free rapid poll feed permission established. Not adopted. |
| AFCA | Official Coaches Poll | Official publisher provenance confirmed; automated reuse permission/cost unestablished | Weekly release, no verified rapid feed or rate limit. CFBD remains existing acquisition route. |
| CFP | Rankings, announcements, selections | Existing dated announcement parser retained; broader machine-feed permission unresolved | No universal rapid selection feed established. Do not infer athletics terms from CFP retail shop terms. CFBD confirmation remains required. |
| SportsDataIO | Schedules, scores, box scores, team/player stats | Commercial license quoted; free trial can scramble data; free Discovery historical | Personal-use data delayed one day. Historical/trial products unsuitable for live publication. No trial started. |
| Sportradar | Scores, schedules, stats, AP/Coaches/CFP | Licensed product, quote/access required | Rankings documented within 15 minutes of public release, hourly recommended pull; does not establish five-minute objective. |
| ESPN | Broad scores/schedules/stats | Existing assessment requires written permission for automated monitoring | Disabled; no undocumented endpoint adopted. |

## Executable acquisition improvements

The existing V8 source collector now reuses its private cached season membership rather than redownloading it every in-season run. A missing cache still uses the normal authorized request and shared reservation. It skips drives for a season type with no completed FBS games. Scores, models, derivation formulas and archives are unchanged. Both changes apply to the existing collector; no competing service or scheduler is created. Regular-season warm refresh falls from seven to five metered calls when exactly two recent play weeks need refreshing (two games batches, one regular drives batch, two play weeks). Cold-cache historical play requests and failures still consume additional attempts; the seven-attempt ceiling remains intact. No capacity savings are claimed when both season types need drive data. Membership is intentionally season-cached; unusual membership corrections need an explicit cache refresh.

## Detection and detail separation

Keep one authorized status batch per active season type, shared across games. Publish verified finals through essential-only refresh and recalculate from retained verified inputs. Retrieve detailed stats separately after essential capacity is available. Poll releases share one rankings batch. Existing CFP dated-page detection cannot be extended to AP/AFCA or selection pages without establishing permission. A lightweight response is not necessarily unmetered. Do not substitute estimated finish time for an actual final flag.

## Reproducible season capacity model

`python scripts/season_acquisition_capacity.py` emits assumptions and endpoint arithmetic without contacting providers. Uses existing collector behavior: status batch per season type; conservative two-call score publication; two call poll publication; warm statistics up to five regular-season calls after this change. Counts are scenario inputs, not measured traffic. Weekday windows, overtime/delays, failure reserve, rivalry, mixed championships and postseason are explicit. A retained FBS calendar cannot predict exact future delays or announcement timing.

Minimum infrastructure option is the existing chained GitHub watcher with enough authorized data capacity, not another timer. GitHub queued starts, six-hour handoffs and deployments have no minute-level SLA. A five-minute detection interval cannot itself guarantee publication within five minutes. The 95% objective requires source observations and actual public verification during new events; the prior unchanged-data receipt-to-observation bound is not a success sample.

## Sources checked

- https://collegefootballdata.com/terms
- https://collegefootballdata.com/api-tiers
- https://api.collegefootballdata.com/api/games
- https://api.collegefootballdata.com/api/drives
- https://api.collegefootballdata.com/api/plays
- https://www.ncaa.org/terms-of-service/
- https://www.ncaa.com/tos
- https://www.statbroadcast.com/terms.php (search retrieval provided text; direct fetch returned403)
- https://www.stats.statbroadcast.com/support/scoreboard-bridge.php
- https://www.ap.org/content/topics/sports/
- https://api.ap.org/media/v/docs/Quota_Limits.htm
- https://www.afca.com/polls/
- https://big12sports.com/sports/2022/9/1/Communications.aspx
- https://sportsdata.io/developers
- https://sportsdata.io/pricing
- https://developer.sportradar.com/football/reference/ncaafb-rankings-current-week

Unknown permissions, negotiated prices, rate limits and reliability commitments require provider confirmation; none were invented. This inventory does not claim exhaustive review of every university or conference contract.

## Final monthly purchase assessment

November27 owner requested all-application monthly budgeting. New reproducible monthly model supersedes the earlier minimal peak estimate for purchase sizing. All numbers are planning allowances, not actual future traffic or measured endpoint latency. Two/three/five-minute regular active union windows are115hours in November (overlapping games share batches). Daily two-call schedule/baseline and two-call markets are included; team/player boxscore allowance is two calls per publication wave; seven-call mixed postseason stats and five-call PR78 warm regular stats are explicit. Cold-cache/correction allowance100/month plus30% contingency. Individual boxscore allowance is future capacity, not a new production feature. Status uses one batch/check; mixed season-type periods can require more. Five-minute cadence cannot assure five-minute end-to-end publication.

| Month | 2 minutes incl contingency | 3 minutes | 5 minutes |
| --- | ---: | ---: | ---: |
| August2026 | 1469 | 1118 | 838 |
| September2026 | 4021 | 2929 | 2056 |
| October2026 | 5342 | 3847 | 2651 |
| November2026 | 5735 | 4136 | 2857 |
| December2026 | 3452 | 2503 | 1744 |
| January2027 | 1650 | 1234 | 901 |

Busiest projected month November; peak-week stress case40activehours,40publicationwaves,2rankingwindows,5statscalls,14baseline,14market,80boxscore,25correction calls totals1482 before30% /1927 after. This weekly stress case can exceed a typical week; monthly allowance is not evenly prorated. Offseason February–July budget100calls/month plus30%=130/month for schedule/stat corrections, no intensive monitoring. Annual two-minute allowance22449 including these six offseason allowances (rounding monthly contingency separately).

Tier1 $1/month ($12/year, or $6 for six active months) is insufficient for the above two-minute stress budget: November exceeds5000 by735. At3min it leaves864 calls beyond already-budgeted contingency but has less latency margin; it is a budget option, not a reliable SLO claim. Recommend Tier2 $5/month ($60/year, or $30 for six active months with free offseason) as the least expensive published tier covering this target scenario with substantial room: November uses19.1% of30000. No purchase. Still no source-first-availability SLA or verified95% performance; sufficient quota alone is not reliability.

Verified published tiers: Free1000/$0; Academic3000/$0 (eligibility required); Tier1 5000/$1; Tier2 30000/$5; Tier3 75000/$10; Tier4 125000/$15; Tier5 200000/$20; Tier6 500000/$30 per month. Annual arithmetic12xmonthly is not a quoted annual billing discount; taxes/checkout charges unknown. Live scoreboard startsTier1, live play-by-play Tier2, GraphQL Tier3. Existing account reset receipt is2026-12-01T00:00:00Z. Future Jan1/Feb1 and subsequent calendar-month resets are planning assumptions: published pages do not establish exact UTC reset rules for every paid tier or whether an upgrade restores already-spent allowance. Verify actual /info.resetAt and entitlement after any owner-authorized upgrade. No new info request spent for this assessment. Shared CFBD/CBBD pool, no quota circumvention, private caching and derived-output use allowed; raw redistribution prohibited. Numeric per-minute API throttle not established by these pages; monthly allowance is not permission for unrestricted bursts.

GitHub cron minimum five minutes, possible delayed/dropped starts and default-branch rules remain separate from API capacity. Existing long-running watcher can sleep at sub-five-minute intervals after it starts, but runner lifetime, queue/handoff, provider delays and Pages publication still have no five-minute guarantee. More quota does not remove these limits. Production quota currently at protected eight-call floor per retained ledger; no floor bypass.
