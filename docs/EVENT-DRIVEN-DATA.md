# Event-driven game-day data

**Principle:** the calendar tells us when to look, the event tells us when to act, and the authoritative source tells
us when to verify. No prediction formula, weight or methodology changes.

## Reliability after the November 24 CFP incident

**What failed (verified from run logs):** the November 24 CFP rankings reached the site only after the owner reported
them, about 1 hour 40 minutes after the usual release time.
- **GitHub scheduling:** none of the poll workflow's 11 scheduled starts in the release window ran. Scheduled runs were
  also starting about 10 hours late (the 11:23 UTC daily refresh ran at 21:20 UTC).
- **Quota:** the watcher had 0 discretionary CFBD calls (40 left against a 42-call reserve), and it detected CFP releases
  only through CFBD, so it could not detect the release at all.
- **Site status:** the footer treated a release as due only 30 hours after its date, so it showed "all current" for six
  hours after the release aired.

**Corrections:**

| Problem | Correction |
| --- | --- |
| CFP detection depended on CFBD quota | The watcher reads the dated official page every 30 s from the announcement time (no CFBD call). Only a complete parse (ranks 1–25, known programs, date stated) spends one CFBD call to confirm every position, retried at 2, 4 and 8 minutes if CFBD lags; `cfp_publish` re-checks both before publishing |
| Releases competed with game monitoring for quota | Releases have a priority allowance that may spend down to an 8-call floor (`RELEASE_FLOOR`): up to 8 calls per CFP release, 10 per AP/Coaches release. When the discretionary budget is empty, one end-of-day publication wave for the day's games is also funded from it |
| AP/Coaches detection | Still CFBD (no reliable machine-readable official source), but paid from the priority allowance and paced over the release window. Scheduled poll runs no longer call CFBD on days when no poll can change (about 24 calls saved per CFP night) |
| Watcher starts depended on GitHub's scheduler | Each watcher run queues its successor when it starts and stays alive until its deadline while the season has games to watch. The concurrency group allows one running and one queued run, so runs never overlap; more than 4 starts in an hour (a crash loop) stops the chain and alerts. The hourly schedule remains a backup |
| A stopped chain went unnoticed | `watch_keeper` runs after the data refresh, the poll refresh, every deployment and every watcher job: it restarts a stopped chain (never a second watcher) and runs a monitor pass |
| Nobody was told | `freshness_monitor` checks missed scheduled runs, a stopped chain, unpublished official releases, finished games not yet published, exhausted CFBD budgets and failed deployments. Alerts go to one GitHub issue ("Data freshness alert"), which is opened, updated only on change, and closed when resolved |
| Footer said "all current" | A CFP release counts as overdue 15 minutes after its scheduled time. Each deployment writes `monitor-status.json` (watcher state + open alerts), and a change in alerts redeploys it; critical alerts and interrupted monitoring replace "all current". The site contacts no third party |
| Duplicate test run in the deploy | The build checkout now has the parent commit (`fetch-depth: 2`), so the validated-refresh skip works (about 20–30 s saved) |

**Publication latency (CFP), by stage:**

| Stage | Before | Now |
| --- | --- | --- |
| Detection | Next CFBD check or poll cron (hours on 24 November) | At most 30 s after the official page appears |
| Verification | — | One CFBD call (about 1 s); more only if CFBD lags |
| Poll workflow | About 15 s plus queueing | Unchanged |
| Build to live | About 2 min 35 s (measured 25 November: commit 01:37:59, Pages 01:40:27) | Unchanged for poll commits, which still run the full suite. Game refreshes save about 20–30 s from the fixed test skip |
| **Total** | 1 h 40 min on 24 November | **About 3.5 minutes at most** (estimated from the measured stages; first real measurement at the 1 December release) |

Each watcher event records `available_after` (the last check that did not see it), `detected_at`, `confirmed_at`,
`dispatched_at` and `published_at`, and the run summary shows detection, verification, publication and total
latency separately.

**External scheduler (not adopted):** the self-sustaining chain plus keepers removes the dependency on GitHub's cron for
normal operation. A free external scheduler (for example cron-job.org) calling `workflow_dispatch` would add a second
restart path, but it needs a fine-grained personal access token with Actions write permission stored at a third party.
That is an owner decision; nothing was purchased or created.

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
| CFBD `/rankings` | AP, Coaches and CFP polls by week | Present on Sunday afternoon (seen during the November 22 window) | Detection for AP and Coaches; `poll_refresh` validates and publishes them. For the CFP it is the independent confirmation of the official page |
| Official CFP release | Dated, sourced CFP rankings | Tuesday evenings | Authoritative, and read directly by the watcher every 30 s during a release (no CFBD call). Published automatically only when CFBD confirms every position |
| Live site (`season-report.json`, `poll-snapshot.json`) | What fans actually see | — | Publication verification |

**Considered and not adopted:** ESPN's undocumented scoreboard API. It is unofficial with unclear terms, and CFBD
already detects finals.

**Provider limits (CFBD verified on 2026-11-22 with `GET /info`):**
- **CFBD account:**

  | Field | Value |
  | --- | --- |
  | Tier | Free (patron level 0) |
  | Monthly limit | 1,000 calls |
  | Reset | First of the month |
  | Used by November 22 | 917 |
  | Remaining on November 22 | 83 (74 after the integration runs) |
  | Cost of `/info` itself | None |

- **Where November's calls went:**
  - 19 runs of the V7 historical backfill (`v7-market-backfill.yml`), about 22 calls each. It is triggered by pushes to
    `v7-development` that touch V7 files, and one was triggered by this branch's first sync.
  - The one-off V8 source acquisition.
  - About 15 calls a day of routine refreshes. The removed 15-minute gate crons spent one call per run.
- **Pacing:** the watcher reads `/info` at the start of each session (`quota_plan`).
  - **Reserve:** it keeps 6 calls a day until the reset for the scheduled workflows (daily baseline, polls, statistics).
  - **Today's share:** it gives today a share of the rest proportional to today's games, always covering the releases
    due today.
  - **Spreading:** it spreads check-and-refresh cycles over today's completion windows.
  - **Pausing:** below the reserve it makes no calls and alerts; the daily baseline still reconciles.

  | Situation | Check interval |
  | --- | --- |
  | Free tier, healthy mid-month Saturday | About 10 minutes |
  | Early month | About 2–3 minutes |
  | November 28, 2026, with the current remaining quota | About every 2 hours (six publication waves) |

- **Do not re-run the V7 backfill or V8 source acquisition in-season.** Each costs tens to hundreds of calls.
- **GitHub Actions:** the repository is public, so standard runner minutes are free. An idle hourly start exits in under
  a minute and makes no CFBD call.

## Postseason and CFP (added after review)

- **`postseason.py`:**
  - **Sources:** CFBD `seasonType=postseason` (conference championships if CFBD files them there, bowls and CFP games).
  - **Outputs:** `data/cfbd-2026-postseason.json` (the watcher's calendar) and `web/public/postseason-2026.json` (the
    site).
  - **Predictions:** the existing official formula applied to the published ratings. Postseason results are not fed
    into the ratings.
  - **Quota:** the CFBD call is skipped before December. Conference championships filed as regular-season games are
    already covered by the main refresh.
  - **Display:** a "Bowls and College Football Playoff" section on Game Predictions, hidden until games exist.
- **`cfp_publish.py`** (run by `refresh-polls.yml`) publishes a CFP release only if every check passes:
  1. the official dated page exists and states its release date;
  2. it parses to ranks 1–25 of known FBS programs;
  3. CFBD's committee poll for its newest week matches at every position;
  4. it is newer than the published release.

  It writes an evidence file like the reviewed November 10 one. Anything else changes nothing and warns.
- **Live check, run 45079999028:** the real November 17 official page and CFBD agreed at all 25 positions ("published
  the 2026-11-17 release (week 12)" in dry run).

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
   - **Starts:** each run queues its successor (watcher chain); the hourly schedule and `watch_keeper` restart a
     stopped chain. A run watches for up to about 6 hours; one concurrency group keeps runs from overlapping.
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

**Publication pipeline (optimized; no validation removed):**
- The data refresh now runs the full Python suite **after** building the new data and **before** committing it, so a bad
  refresh is never committed. Previously it ran before fetching.
- The dashboard skips its duplicate run only for that exact validated bot commit.
- Measured on production runs: refresh about 55 s, then build about 2 min 45 s (including about 36 s of tests, now
  skipped for validated refresh commits), then the site is live about 15 s into the deploy job.
- **Estimated dispatch-to-live:** about 3.5 minutes. The deploy job's 2 minutes of live verification run after
  publication.

**The 5-minute objective, end to end:**
- **Free tier:** met only when the month's quota allows checks about every 2 minutes (early month). A healthy mid-month
  Saturday checks about every 10 minutes, so about 9 minutes on average.
- **Paid CFBD tier:** sustained 2-minute checks would meet it on every Saturday. That is an owner decision; no paid tier
  was assumed.

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
- **CFP:** publication requires the dated official release and CFBD agreement; if CFBD never agrees, an alert is raised
  and nothing is published.
- **AP/Coaches:** detection still depends on CFBD and the priority allowance; with little quota left, checks are about
  every 30–50 minutes in the release window.
- **Postseason:** bowl and playoff games use CFBD `seasonType=postseason`, which neither the refresh nor the watcher
  reads yet.
- **Provisional statistics:** none are published. CFBD `/games` already delivers final results, so no second, faster
  provider was justified.
