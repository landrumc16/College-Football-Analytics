# November 26 Game Freshness Incident

## Status: Production Recovered; PR #73 Awaiting Owner Merge Approval

Authorized current-main refresh run **45944035791** succeeded. Data commit:
`771c1d04afaf8002500e2de06b9c0e30b167d80d`. Deployment **45944161131** succeeded,
including live desktop/mobile/PWA verification. No correction code has been merged.

| Event | Verified timestamp (UTC, November 27) | Central (November 26) |
| --- | --- | --- |
| ESPN end-of-fourth-quarter play wallclock | 04:29:20 | 10:29:20 PM |
| First retained observation of ESPN final | 04:48:23 | 10:48:23 PM |
| Fresh current-main dispatch | 05:08:56 | 11:08:56 PM |
| Successful CFBD source receipt containing 48–27 | 05:09:18.287734 | 11:09:18 PM |
| Production automated HTTP/content smoke passed | 05:12:44 | 11:12:44 PM |
| First separate public final-score observation | 05:13:08.507081 | 11:13:08 PM |
| Full live desktop/mobile/PWA verification completed | 05:14:37 | 11:14:37 PM |
| Deployment job completed | 05:14:53 | 11:14:53 PM |

The ESPN wallclock is a provider-reported end-of-period timestamp, not an independently
observed stadium clock. CFBD's first availability is unknown; 05:09:18 proves availability
by that receipt. Publication is proven by the 05:12:44 smoke check; exact first serving time
is not known. Do not substitute build-generation time for source freshness.

### Production Acceptance

- Public final: Texas Tech 48, TCU 27. Records 11–1 / 5–7; Big 12 records 8–1 / 3–6.
- Existing model recomputed Texas Tech strength from 18.271705 to 18.747195; model rank
  remains #8. TCU is #73. Formula/code unchanged.
- Current last-three level: 30.0793. Schedule and team intelligence use the new receipt.
- Public report/scenario SHA pair matches. Texas Tech/TCU is excluded from remaining-game
  options. Real browser team schedule shows W 48–27 Final; scenario baseline renders.
- Existing CFP simulation includes the final and reports Texas Tech field estimate 100%,
  conference-title estimate 43.73%. These retain the existing approximate conference/committee
  assumptions and are not official clinching probabilities; rules/model replacement is out of scope.
- Other newly completed game: Alabama State 45, Tuskegee 0. No past-due pending FBS games
  remain in the refreshed source. Fourteen lower-division pending rows remain provider gaps;
  none is an FBS matchup. They are not falsely filled or asserted to be completed games.
- All 240 immutable pregame files remain byte-identical; no postgame backfill. Official
  legacy scorecard evaluated games increased 192 → 193. Separate strict V9 comparison now
  has one common game: all three models picked Texas Tech. This is insufficient to rank models.
- Archived first pregame margins: Official 11.9952, Standard 9.47, Momentum 10.76; actual
  margin 21. Public accountability scores the retained probabilities without rewriting them.
- Important remaining data limitation: advanced EPA/play, drive and four-game unit trends
  still carry the November 22 18:02:41 UTC receipt, explicitly stale in team intelligence.
  The independent V8 refresh costs approximately seven calls with a populated private cache
  (more if missing). It was not launched while the remaining quota and eight-call reserve
  cannot be guaranteed. Scores/records/strength freshness must not imply these unit stats updated.
- Physical-device testing is not claimed; automated browser/PWA checks passed.

## Verified Evidence

- Big 12 official release reports Texas Tech 48, TCU 27:
  https://big12sports.com/news/2026/11/27/football-texas-tech-secures-berth-in-edward-jones-big-12-championship-will-face-utah.aspx
  On-page publication dateline: November 26, 10:34:43 PM; final-whistle time and dateline timezone were not independently verified.
- ESPN summary for event 401856879 observed at 2026-11-27 04:48:23 UTC
  (November 26, 10:48:23 PM Central): final 48–27; Texas Tech 11–1, conference 8–1;
  TCU 5–7, conference 3–6. This is observation time, not provider-first-availability time.
- Public season-report.json still had source receipt 2026-11-26 20:28:19 UTC
  (2:28:19 PM Central), and this game pending. Kickoff was November 26, 7 PM Central.
- Watcher run 45887932014 was created at 20:01:17 UTC; its actual job 140262563227
  started November 27, 01:46:38 UTC. It was running during the game's completion window.
  An old run creation timestamp alone does not prove watcher downtime.
- Freshness issue #71 at 04:10:26 UTC reported 20 CFBD calls left, four days to reset,
  zero discretionary budget and a delayed scheduled backup. The active watcher was still running.
- Exact unchanged-main quota-policy replay using that reading and the committed schedule
  at watcher start returns budget 0, priority budget 5, wave_at **November 28 02:15 UTC**
  (**November 27 8:15 PM Central**). It combines games in the next 24 hours, so tomorrow's
  games postpone tonight's supposed end-of-day fallback. This is a policy replay; the active
  job's full logs/ledger were not downloadable while it ran.
- Time-based overdue-game monitoring waits until kickoff + 4h45m + 30m, or November 27
  12:15 AM Central for Texas Tech, rather than observing the actual final. Therefore its
  lack of an immediate stale-final critical alert is explained by its code, not evidence of current data.
- Recovery rerun of refresh run 45891224744, attempt 2, started at 04:50:46 UTC.
  CFBD fetch succeeded by 04:50:59.991 UTC; completed count increased from 3,645 to 3,647.
  Exact provider-first-final time and per-game final content were not retained in accessible output.
  Do not infer those timestamps or scores solely from the aggregate count.
- That job passed 836 tests, 5 skipped, before publication, but its original SHA checkout
  caused data conflicts during rebase at 04:51:37 UTC. It failed closed; no refresh commit
  reached main. No further historical-job reruns should be attempted.
- Today's ESPN FBS scoreboard lists only Texas Tech/TCU. Other overdue pending source
  rows include Alabama State/Tuskegee and Concord/Ferrum. Confirm their disposition from
  the fresh CFBD snapshot; do not guess or fill cancelled/missing games with zeroes.

## Root Cause and Proposed Correction

The quota policy disables ordinary game checks, leaves only a late publication wave,
and merges tomorrow's completion windows into that wave. The monitor warns about quota
but cannot recognize an actual early final independently of CFBD polling. A running
watcher consequently does not guarantee prompt score publication. GitHub scheduling
delay is a secondary operational constraint, not sufficient evidence for tonight's root cause.

Proposed branch correction:

1. Read ESPN's public FBS final-status signal every two minutes during scheduled completion
   windows when discretionary checks are unavailable. Require matching event id, exact kickoff,
   complete status and valid scores. Never use secondary scores as published/model inputs.
2. Wake existing CFBD confirmation, existing data-refresh workflow and live-site verification.
   Cap signal-triggered confirmations at three per session, charge failed calls too, reserve
   refresh and one retry when affordable (up to 11 calls in the shared game allowance), and
   preserve the eight-call floor. A healthy final still spends only five calls. Actual provider/deployment latency
   remains external; bounded retries can exhaust before a lagging provider agrees.
3. Restrict timed fallback to today's/overdue games; late-starting sessions still fund recovery.
   Retain that fallback when the free signal fails. At the quota floor, alert instead of publishing.
4. Escalate an observed final awaiting CFBD confirmation/reserve as a critical monitor condition.
   Label time-only overdue checks honestly rather than asserting an unverified final.
5. Fresh refresh runs/reruns check out the current requested branch head before reading
   append-only archives. Any staged path changed upstream stops publication before rebase, even for textually mergeable
   data. Non-overlapping production fixes are rebased safely; rebase failure aborts cleanly.
   A fresh current-main run re-derives data. Unfunded dispatch retries are withheld and alerted;
   no force-push, automatic conflict overwrites or weakened checks.

## Recovery Procedure (Executed Successfully; Retained as Runbook)

The connector exposes rerun, but no fresh workflow-dispatch operation. GitHub browser is
signed out and local gh has no authenticated account. Normal GitHub authentication is
needed once; do not ask for or copy API secrets. After sign-in:

1. Run **Refresh college football data**, branch **main**, season **2026**, once.
2. Confirm source final 48–27, successful validations, data commit and downstream Dashboard
   workflow completion. Do not deploy this unapproved correction branch.
3. Compare old/new schedules, all newly completed ids and other overdue rows. Confirm Texas Tech
   11–1/8–1 and TCU 5–7/3–6; rankings, postseason inputs and paired scenario report use the same receipt.
4. Diff pregame archives against b3b80810: prior files must remain byte-identical. Confirm
   prediction accountability scores existing pregame forecasts and never adds postgame backfills.
5. Verify actual public report, scenario payload and browser result; record source receipt,
   data commit, successful deployment completion and first observed public publication separately.
6. Finish this record, then request owner approval for the correction PR. No code merge authorized.

## Verification

Permanent tests cover early actual final, CFBD lag/recovery, never publishing secondary scores,
failed-call accounting, free-source failure/timed fallback, no-reserve behavior, event identity,
late starts, next-day window isolation and critical final alerts. Live free-signal adapter recognized
401856879 with zero CFBD calls. Existing prediction functions, frontend, historical data and
archives have no changes in this correction.

Physical-device testing is not claimed. No service purchases or new subscriptions.

### Authentication and CI Follow-up

Google sign-in was selected through the secure authentication flow. Google then reported
that phone approval was declined. No automatic retry or alternative-account switch was
attempted. Recovery still requires an authorized fresh main workflow dispatch.

Initial remote CI exposed two legacy release-manifest tests hashing current HEAD against
historical approved-content pins. Local pre-commit execution had hashed the old HEAD.
Keep those old manifests unchanged as historical fixtures; new maintenance tests pin the
actual committed correction and prove branch/fork/content/model/data rejection. The guard
implementation and protected path lists are unchanged. New exact manifest is pending owner
review; its presence is not owner merge approval.

### PR #73 Final Acceptance Scope

Thursday/Friday/Saturday simulated clocks must each publish within five minutes when both
providers are current and the deployment takes three minutes. This is deterministic latency
validation, not a claim that external providers/GitHub meet an unconditional SLA. At the quota
floor, provider delay or failed deployment, publish no invented score; emit an immediate
critical monitor pass, retry only within funded limits and retain a current-day timed fallback.

The actual publication shell script is exercised against local bare Git remotes: preserve
non-overlapping newer changes and pregame bytes, refuse overlapping data/archives without
pushing, leave readable JSON, recover through a fresh validated current-main run, and avoid
no-op commits. Existing full source protections remain in effect via exact proposed-content
pins. Owner merge approval is still required after acceptance.

### Executed Local Acceptance Results

- Full suite after reconciliation with recovered main: **863 passed, 2 skipped**.
- Focused watcher/calendar/monitor/publication-recovery suite: **58 passed**.
- Previously committed PR #73 CI passed before the final weekday/recovery additions.
  Final remote CI must be checked at the final PR SHA; no earlier green run substitutes for it.
- Production data refresh: **836 passed, 5 skipped** on its GitHub Python-only runner;
  dashboard build and live desktop/mobile/PWA verification succeeded. Different runner
  dependency availability explains the different skips; no skipped check is claimed executed.
- Remaining constraints: provider-first-availability unknown, advanced unit stats dated
  November 22, finite CFBD monthly quota, GitHub scheduling/deployment latency, and no physical-device test.

Final CI additionally caught a source-transfer truncation in the draft branch. It never
reached main. Final acceptance requires exact Git tree identity between the tested local
checkout and the GitHub commit, plus fresh CI at that commit. The game retry guard is
explicitly scoped to game refreshes; the existing discretionary CFP path has a regression test.
