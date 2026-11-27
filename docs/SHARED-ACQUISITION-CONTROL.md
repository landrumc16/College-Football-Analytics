# Shared acquisition control — pending owner approval

Issue #74 remains open. This is a combined acquisition pass, not Version 10 or a
claim that 95% of updates reach production within five minutes.

## Operational behavior

All current CFBD source clients use one transport. On credentialed Actions runs,
each metered attempt first reads `/info`, reserves capacity through GitHub Contents
SHA compare-and-swap, then contacts CFBD. The state lives only on
`operations/quota-ledger`, never on main; no credentials or raw source payloads
are stored. Eight bounded CAS retries handle contention. Unknown provider quota,
failed ledger access, conflicts exceeding the retry bound or exhausted capacity
prevent the source request. Nothing force-pushes or overwrites concurrent state.
Failed source calls and retries consume reservations, including a source attempt
whose process crashes before its result is known. Those reservations are not
optimistically refunded. A verified new reset period starts a fresh ledger.

Essential current-season games/rankings reserve down to the existing eight-call
floor. Core endpoints retain twelve additional essential calls. Supplemental and
historical retrieval retain another seven core calls. Workflow preflights remain
more conservative where applicable. Per-run limits persist across processes and
job steps: watcher 400 maximum (its existing pacing usually grants much less),
statistics acquisition seven attempts including cold-cache misses/retries, other
source workflows eight attempts. These are ceilings, not entitlements to spend.
The broker can govern updated repository clients, not outside clients using the
same account or reruns checked out at old, uninstrumented revisions.

Source-capable steps receive the existing GitHub token only at those steps.
Contents write is needed to reserve quota; it does not grant new secrets or external
accounts. Existing keeper tokens and workflow concurrency are preserved. All
source-capable current workflow definitions are configured; forks do not receive
source secrets. Source jobs must use the current reviewed checkout, not old reruns.

Watcher-triggered refreshes set `essential_only=true`. Optional market acquisition
is excluded entirely from this path; regular and postseason scores cost at most
two CFBD calls. Core statistics remain an independent workflow. Offline report,
ratings, projections and accountability calculations reuse retained verified data.
The normalizer and all prediction calculations are unchanged. Existing private
historical/play caches remain the means of avoiding repeated historical retrieval.

The watcher reuses one batch per season type rather than one request per game.
Only FBS-related games (including verified existing aliases and FCS opponents of
FBS schools) compete for its calendar budget; full source archives are untouched.
New FBS matchups discovered in a fetched batch join the same in-memory calendar.
Actual final flags and changed kickoff timestamps continue to drive completion and
rescheduling; estimated finish times alone never establish a final. Unknown live
period/overtime status is not invented from a source that does not provide it.

Latency reports now leave total availability-to-publication unknown when there
was no prior observation of that game's source state. Per-game observations avoid
borrowing another game's check time. First authoritative availability is explicitly
null unless separately established; detection/receipt/publication observations
remain separate. An unknown interval cannot count as a five-minute success. Even
consecutive provider observations are observational evidence, not proof of globally
consistent provider-first-availability. The 95% objective remains unverified.

## Verification and rollout

Unit/lifecycle tests cover contention, source failures before retry, persistent
limits across process restart, floor/priority protection, monthly reset, unknown
quota, newly discovered FBS games, essential-only dispatch and honest latency.
A separate CI job exercises genuine GitHub CAS with concurrent clients on an
isolated per-run test branch. It makes zero CFBD requests, retains a JSON receipt
and removes its test branch. That proves coordination mechanics, not live source
entitlement or publication latency.

After explicit owner approval only: merge and verify deployment, safely replace
the single old watcher with approved main, observe ledger initialization and fresh
source attempts, and retain real event timestamps during rivalry weekend. Do not
call historical provider dry runs to prove the ledger. Missing source quota must
alert rather than fabricate results. Existing safe refresh publication and live-site
verification remain required before an event is complete.

## Capacity and source assessment (November 27, 2026)

Reproduce estimates with `python scripts/acquisition_capacity.py`. The generated
JSON lists every assumption and makes zero provider requests. These are scenario
estimates, not production measurements or a service-level guarantee.

| Assumed event window | Two-minute checks plus essential publication | Five-minute checks plus essential publication |
| --- | ---: | ---: |
| Ordinary Saturday: 12 hours, 15 waves | 390 | 174 |
| Rivalry weekend: 16 hours, 24 waves | 528 | 240 |
| Championships: 8 hours, mixed season types, 6 waves | 492 | 204 |
| Postseason month: 60 active hours, 20 waves | 1,840 | 760 |

An assumed four-ordinary-Saturday month plus narrowly targeted poll windows,
weekly core statistics and daily essential reconciliation totals **1,784** calls
at two-minute detection, or **920** at five-minute detection, before unforeseen
retries/provider delays. The account's documented free allowance is **1,000/month**.
Five-minute detection can itself exceed five minutes end to end. Therefore the
present free resources do not justify promising the target cadence for a season.
Batching and removing optional retrieval reduce waste, but cannot create quota.

| Source | Assessment and adoption |
| --- | --- |
| Existing CFBD games/rankings/statistics | Existing authorized account; batched current endpoints remain primary. No new paid access assumed. |
| CFBD live scoreboard | Official tier comparison places live scoreboard in paid access; old beta statements about unmetered live requests do not establish this free account's entitlement. Not enabled or probed. |
| Existing official CFP release | Existing dated-page parser and CFBD confirmation retained. Actual next-release latency still needs measurement. |
| AP sports/Media API | AP offers licensing including Top 25; no existing project license or free rapid machine feed established. Not adopted. |
| AFCA/Coaches official page | Useful authoritative poll provenance, but no permitted reliable rapid machine endpoint established. Not adopted as an automatic source. |
| Sportradar rankings | Documented licensed API, but provider says updates within 15 minutes and recommends hourly non-live retrieval; does not establish our five-minute objective. No subscription created. |
| ESPN public endpoint | Remains disabled absent established written authorization. Public access/client libraries do not establish permission. |

Primary references checked:
- https://api.collegefootballdata.com/usage-and-access
- https://collegefootballdata.com/api-tiers
- https://www.ap.org/content/topics/sports/
- https://www.afca.com/polls/
- https://developer.sportradar.com/football/reference/ncaafb-rankings-current-week
- https://docs.github.com/en/actions/reference/limits
- https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

GitHub's existing continuous watcher can make sub-five-minute checks while a runner
is active, but scheduled starts and runner handoffs are not punctuality guarantees.
The ledger adds roughly one GitHub read/write pair per source attempt, plus setup
when absent; that is modest under modeled two-minute batches but introduces a
control-plane dependency and must be observed under production load. No external
scheduler, hosted service or subscription was purchased or created.

## Still open

Permitted rapid AP/Coaches detection, comprehensive official selection ingestion,
long postponement/cancellation disposition, source-first-availability measurement,
real GitHub/source outage recovery and full-season performance need operational
proof. Outside/old clients and conservative crashed-attempt reservations remain
coordination limits. Hourly audits are oversight only, not active monitoring.
