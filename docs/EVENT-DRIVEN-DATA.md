# Event-driven game-day data

**Principle:** the calendar tells us when to look, the event tells us when to act, and the authoritative source tells
us when to verify. No prediction formula, weight or methodology changes.

## Audit: what was wrong (measured, November 7–22, 2026)

| Finding | Evidence | Effect |
| --- | --- | --- |
| GitHub honors the 15-minute crons only every 3–4 hours | 6–10 "Refresh college football data" runs per game day on November 7, 14 and 21, none cancelled. **Zero** poll-refresh runs between 16:00 and 20:00 UTC on Sunday, November 22 | Finals and polls appear hours late even when every workflow is healthy |
| Poll and statistics commits never deployed | `dashboard.yml` ran only after the game refresh. Bot pushes made with `GITHUB_TOKEN` do not trigger workflows | A new AP or Coaches poll waited for the next game refresh to go live |
| Nothing verified the live site | Deploys could fail or be cancelled (PR #49's deploy was cancelled mid-flight) and nothing noticed | Stale data could be served while a workflow reported success |
| On November 22 the week-13 AP and Coaches polls and the week-12 CFP rankings were in CFBD | `event_watcher --dry-run` on GitHub Actions (run 45066715851) found AP 13, Coaches 13 and CFP 12; the live site showed weeks 12, 12 and the November 10 CFP release | This is the user-visible symptom of both findings above |

The pipeline itself is fast once started: a refresh takes about 1 minute and a build plus deploy about 4.9 minutes
(median of the last 15 deploys).

## Sources

| Source | Provides | Speed | Role |
| --- | --- | --- | --- |
| CFBD `/games` | Scores, completion, kickoff changes | Finals detected by the existing gate within one check of CFBD marking them complete | **Both fast and authoritative.** The refresh already uses it, so detection and publication agree. No second provider was added |
| CFBD `/rankings` | AP, Coaches and CFP polls by week | Present on Sunday afternoon (seen during the November 22 window) | Fast detection for AP and Coaches; `poll_refresh` validates and publishes them. CFP rows are undated, so they are **alert-only** |
| Official CFP release | Dated, sourced CFP rankings | Tuesday evenings | Authoritative. Stays a manual, verified publication (an existing rule) |
| Live site (`season-report.json`, `poll-snapshot.json`) | What fans actually see | — | Publication verification |

**Considered and not adopted:** ESPN's undocumented scoreboard API. It is unofficial with unclear terms, and CFBD
already detects finals.

**Provider limits:**
- **CFBD:** every call counts against the account's monthly quota. The watcher checks every 5 minutes only while a game
  is in its completion window or a release is due (15 minutes while games are in progress), and caps each run at 400
  calls (`CFBD_CALL_BUDGET`).
  - A busy Saturday is roughly 150–250 calls.
  - **Check the account tier.** A free tier cannot cover every Saturday at this cadence. Raise or lower
    `WATCH_ACTIVE_SECONDS` to match the tier.
- **GitHub Actions:** the repository is public, so standard runner minutes are free. An idle hourly start exits in under
  a minute and makes no CFBD call.

## Architecture (reuses the existing pipeline)

1. **`src/cfb_analytics/event_calendar.py`** (pure functions):
   - **Game completion windows:** from kickoff + 2h15 (early finish) to kickoff + 4h45 (overtime). After that a game is
     "overdue" for 36 hours (delays, suspensions), then the daily baseline refresh reconciles it.
   - **Poll window:** Sunday 11:00–16:00 Central for the correct poll week (the poll released after week N is week
     N + 1). A late poll stays overdue through Monday.
   - **CFP windows:** the published release dates.
   - It never assumes an event happened.
2. **`src/cfb_analytics/event_watcher.py`:** each check runs the calendar plan, then:
   - checks CFBD `/games` (parsed with the pipeline's own ingestion) and, in a release window, `/rankings`;
   - detects finals, **corrections to already-final scores** (watched for 3 hours after each final), rescheduled
     kickoffs, and new poll weeks;
   - dispatches the existing `refresh-data.yml` or `refresh-polls.yml` (`workflow_dispatch` is allowed from
     `GITHUB_TOKEN`). Simultaneous finals produce one dispatch;
   - verifies that the change is visible on the live site and records detection-to-publication latency. A change still
     not visible after 20 minutes is re-dispatched once, then alerted;
   - handles failures safely:
     - stale responses (a final game reported as not final, an older poll week) are ignored and logged;
     - duplicates are keyed by game and score;
     - each source backs off on its own, so a rankings outage does not stop game monitoring.
3. **`.github/workflows/event-watcher.yml`:**
   - **Starts:** hourly scheduled starts. A run watches continuously for up to about 6 hours, and later starts queue
     behind it (one concurrency group), so dropped cron starts no longer matter.
   - **Ledger:** each run's ledger (`event-ledger.json`) and summary table are kept.
   - **Integration check:** a push to `v7-development` runs the provider dry run.
4. **`dashboard.yml`:** also publishes after "Refresh official college football polls" and "Refresh V8 offense and
   defense statistics".
5. **Footer:** freshness per area (scores and records, model rankings, AP Poll, Coaches Poll, CFP). Each area shows
   current, delayed (no check for more than 26 hours), awaiting verification (a CFP release is due but not verified) or
   unavailable. This replaces reliance on one global timestamp.

**Not changed:**
- the existing refresh, gate and daily baseline workflows (they remain the backup reconciliation);
- the CFP manual verification rule;
- every model.

## Service levels

Latency once an event is detected was measured from production runs: refresh about 1 minute plus build and deploy
about 4.9 minutes, so about 6 minutes. With checks every 5 minutes:

| Measure | Value |
| --- | --- |
| Expected detection-to-publication | About 6 minutes |
| End-to-end, from availability in CFBD | Median about 8.5 minutes, worst about 11 minutes |
| Previously | Hours (one cron start every 3–4 hours) |

**The 5-minute objective is not met yet.** Meeting it needs two things:
- checks every 2 minutes (`WATCH_ACTIVE_SECONDS=120`), if the CFBD tier allows;
- a slimmer publish job. The current deploy also reruns the backtest, the parity audit, the Python suite and preview
  builds on every refresh.

The watcher's ledger reports the real latency of every event once it runs on `main`.

## Tests

**Lifecycle tests** (`tests/test_event_driven.py`, 13 scenarios): each runs the real watcher loop against a simulated
clock and providers, and a site that deploys 6 minutes after a dispatch. They cover:
- simultaneous finals (one dispatch, published within 8 minutes);
- an early finish, an overtime game that becomes overdue, and a weather delay with a rescheduled kickoff;
- duplicate detections, and an authoritative correction 2 hours later;
- a stale source (no regression), a 15-minute CFBD outage, and a rankings outage while games continue;
- a failed dispatch then retry, and a deploy that never shows the change (one re-dispatch, then an alert);
- recovery after overnight downtime;
- Coaches earlier than AP, a late AP poll, and a CFP release (alert only);
- the CFBD call budget.

**Freshness unit tests:** `web/tests/data-freshness-unit.mjs`.

**Integration:** `event_watcher --dry-run` on GitHub Actions against real CFBD `/games` (3,758 games, 0.6 s) and
`/rankings` (0.6 s), the GitHub workflows API, and the live site — all passed in run 45066715851.

## Rollout (after owner approval)

1. Merge into `main`. The hourly watcher, the dashboard triggers and the footer go live together, and the existing
   workflows keep running unchanged.
2. Confirm the first sessions in the event-watcher run summaries (plan, CFBD calls, events, latency).
3. Tune `WATCH_ACTIVE_SECONDS` to the CFBD tier.
4. Optionally build a slimmer publish path to reach the 5-minute objective.
5. Remove `.github/release-manifests/v7-event-driven-protected-changes.json` and restore the strict guard test, as in
   earlier closeouts.

## Remaining gaps

- **5-minute objective:** not met; see Service levels.
- **CFP:** detection is alert-only. Publishing still requires the dated official release.
- **Postseason:** bowl and playoff games use CFBD `seasonType=postseason`, which neither the refresh nor the watcher
  reads yet.
- **Provisional statistics:** none are published. CFBD `/games` already delivers final results, so no second, faster
  provider was justified.
