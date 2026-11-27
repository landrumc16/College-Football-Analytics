# November 26 Game Freshness Incident

## Status: Production Recovery Awaiting Authenticated Workflow Dispatch

Production is not yet restored. No code changes have been merged. Production main remains
`b3b80810b83a2964e0240096bb178ad64d71c4e0`. This record must be completed after recovery.

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
   four calls for refresh, and preserve the eight-call floor. Actual provider/deployment latency
   remains external; bounded retries can exhaust before a lagging provider agrees.
3. Restrict timed fallback to today's/overdue games; late-starting sessions still fund recovery.
   Retain that fallback when the free signal fails. At the quota floor, alert instead of publishing.
4. Escalate an observed final awaiting CFBD confirmation/reserve as a critical monitor condition.
   Label time-only overdue checks honestly rather than asserting an unverified final.
5. Fresh refresh runs/reruns check out the current requested branch head before reading
   append-only archives. Concurrent data conflicts still fail closed; no force-push or weakened tests.

## Recovery Continuation

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
