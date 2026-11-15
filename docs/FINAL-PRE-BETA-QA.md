# Final pre-beta QA review — Texas Tech fan beta

Date: November 15, 2026. Scope: final QA gap review before inviting 25–50 fans.
Version 6 stays closed. This review changed no application code, data, engine or design.

**Recommendation: CONDITIONAL GO.** See §6 for the two conditions.

Tested source: `main` = `ae15ad13c3da7dad5ea3d5416fa25819bf113ea6` (PR #30 merge).
It was deployed by [run 43727666899](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43727666899),
which passed the build, deploy, live browser/PWA and controlled PostHog delivery steps.
Live assets at test time: `index-BYo-bNpD.js` and `index-CxI0pmFV.css`. The live
`season-report.json` SHA-256 was `dc82927a…c37102`, retrieved 2026-11-15 13:48 UTC.
Machine-readable receipt: [`evidence/final-pre-beta-qa-2026-11-15.json`](evidence/final-pre-beta-qa-2026-11-15.json).

## 1. Coverage matrix

| Area | Already verified (prior evidence) | Executed in this review | Result | Gap left |
| --- | --- | --- | --- | --- |
| Chromium functional journeys, five widths | V6 acceptance, PR #29/#30, every deploy (`mobile-smoke.mjs`) | Live journeys during the a11y/privacy harness | Pass | — |
| Firefox | None | **PENDING:** deferred by the owner until computer access (binary download) | Pending, not pass or fail | Run when access allows |
| WebKit / Safari (iPhone) | None | **PENDING:** deferred by the owner (binary download); physical iPhone check in §5 | Pending, not pass or fail | Most likely fan browser |
| Accessibility | Nav dropdowns ≥44 px; focus styles in CSS; no audit tool ever run | axe-core WCAG 2.2 A/AA on 5 destinations at 390/1280; 60-stop Tab walk; touch-target scan; reflow at 320 px and at 640 px (200% zoom); 200% root text; forced colors; reduced motion; light scheme | 1 rule failing (D2); everything else passes; no contrast violations; forced colors legible | Real screen readers (pending) |
| Security / privacy | Secret scan of 1,609 blobs; runtime `npm audit` 0; consent/GPC/DNT unit and CI tests | Probed 20 sensitive paths on live; scanned live bundle; checked headers; `npm audit` (runtime and all); first-visit storage, cookies and outbound requests (default and GPC); outbound link inventory | No exposure; no request before consent; only key stored is favorites; 2 outbound links (PostHog privacy, GitHub issue form) | PostHog project settings (owner, pending) |
| Data integrity / accuracy | 25/25 CFP positions; byte/SHA parity; adversarial malformed-publication containment (PR #29) | Live JSON audit; independent recomputation of all 138 W–L records from the raw snapshot; live report vs. checked-in report; prediction winner/margin/probability consistency; CFP sums; poll name matching in the live UI | Data correct; **D4:** AP/Coaches name mismatch shows Miami (FL) as Unranked | — |
| PWA assets / load | Emulated install/update/offline every deploy | Live manifest, all 4 icons (types and dimensions), offline page, worker; 3 cold loads at 390 px with 4× CPU throttle | Pass; Featured Matchups visible in 0.70–0.79 s, 158–224 KB transferred | Physical install (pending) |
| Scheduled-update recovery | Unit tests for empty, cross-season and duplicate responses | 12 isolated fault injections through the real refresh, report and workflow gate code | **D1:** truncated or regressed responses publish | — |
| Operations | Deploy-time live smoke; 72 h stale gate; client 72 h stale banner | Reviewed Actions history and workflows | D3, L7, L8 | No error monitoring by default |
| Physical devices | **None** (all PWA/Android evidence is emulation) | None possible here | — | **Required (§5)** |
| First-time-user usability | None (automated only) | None (AI interaction is not equivalent) | — | **Required (§5)** |
| Regression | 549 tests at prior closeout | `pytest -q` and `npm run build` at `ae15ad1` | 554 passed; build passed (CSS hash identical to live) | — |

## 2. Commands and environment

Environment: Linux container, Node 22.23.4, Python 3.13.18, Playwright 1.63.0
(headless Chromium only), axe-core 4.10.3. Production traffic was read-only.
The harness blocked all third-party requests and never opted in to analytics.
There was no load testing.

```sh
python -m pytest -q                                   # 554 passed
cd web && npm install && npm run build                # passed
npm audit --omit=dev; npm audit                       # 0 runtime; dev-only vite/esbuild advisories
npm i --no-save axe-core@4.10.3 playwright && cd ..
node web/tests/qa/production-a11y-privacy.mjs         # writes web/qa-evidence/results.json
NODE_USE_ENV_PROXY=1 node web/tests/qa/production-pwa-render-perf.mjs   # proxy flag only needed behind a proxy
git worktree add --detach /tmp/wt HEAD && cd /tmp/wt && pip install pyyaml &&
  python scripts/qa_refresh_fault_injection.py /tmp/wt   # disposable worktree only
```

Both harnesses were run twice with identical outcomes. They are new test-only files
and do not change application behaviour.

Firefox and WebKit are **pending, not failed or passed**. Their browser binaries
come from `cdn.playwright.dev`. The owner deferred that network permission until
they have computer access. Browser coverage in this review is Chromium only.

## 3. Findings

### Verified defects

**D1 — High. Not a beta blocker if condition 2 is met. A well-formed but incomplete CFBD response is published.**
I fed the real `refresh`, then `report`, then the refresh workflow's kickoff and
ledger gates, then the dashboard's pre-deploy report validation. These all passed
and would have committed and deployed:

| Injected response | Published result |
| --- | --- |
| First 15% of games only | 550 completed games; Texas Tech **#18, 2–0** |
| Only weeks 10–15 | Texas Tech **#6, 2–0** |
| 400 completed games reverted to unplayed | 3,053 completed; 633 "upcoming" |
| 200 final scores swapped home/away | Texas Tech #11, 8–2 (actual #10, 9–1) |

The pipeline correctly rejected, and left the last good snapshot untouched, for:
HTTP 503, timeout, truncated JSON, an error object, an empty list, a negative score,
and missing kickoff timestamps.

The damage would be transient. The next good refresh restores correct data, and the
immutable pregame ledger is protected because a past-kickoff game is never recorded.
But fans would see plausible, wrong records until then.

*Smallest proposed correction (awaiting approval):* in `refresh.py`, before the
atomic write, compare against the existing valid snapshot. Fail closed if:
- any previously completed game is missing or no longer completed;
- any previously final score changed;
- the scheduled game count drops by more than 10%.

Add a manual `workflow_dispatch` override input for genuine score corrections.
This is about 15 lines plus tests, with no model or data change.

**D2 — Medium. Not a blocker. Scrollable tables can't be reached by keyboard (axe `scrollable-region-focusable`, WCAG 2.1.1).**
This affects the CFP projections table on Playoffs at 1280 px. At 390 px it affects
4 Playoffs regions and 1 Research region. A keyboard-only user can't scroll the
hidden columns.

*Proposed correction:* add `tabIndex={0} role="region" aria-label="…"` to those
`.table-wrap` elements in `main.tsx` and `PredictionResearch.tsx`. Markup only.

**D3 — Medium (operations). Not a blocker. Game-day refresh runs far less often than scheduled.**
The cron asks for every 15 minutes during game hours. GitHub actually started
refresh runs at:
- Nov 14: 01:57, 05:53, 13:19, 17:11 and 20:22 UTC;
- Nov 15: 00:02, 05:54 and 13:47 UTC.

That is 54 runs in total since Nov 5. GitHub delays or drops scheduled runs. Final
scores can therefore lag by hours. Home shows only "Checked Nov 15", with no time.
Mitigation: tell fans the app is a forecast snapshot updated a few times a day, not
live scores. Optionally, the owner can trigger a manual refresh after Texas Tech games.

**D4 — Medium. Recommended before invites; not a hard blocker. Miami (FL) loses its AP and Coaches rank.**
The published poll snapshot lists AP and Coaches entries as CFBD names them
(`Miami`: AP #5, Coaches #6). The model and the CFP snapshot use `Miami (FL)`, and
the web app matches names exactly. Observed in the live UI:
- the Miami (FL) Team Profile shows **AP Poll: Unranked, Coaches Poll: Unranked**;
- Rankings → AP Poll shows two rows, `Miami — 5 6 —` and `Miami (FL) 3 — — 7`.

Every other AP/Coaches team matches. The cause is that `poll_refresh.py` does not
apply the verified alias map that `pipeline.py` and `report.py` already use
(`Miami`→`Miami (FL)`, `App State`, `Sam Houston`, `UL Monroe`).

*Smallest proposed correction (awaiting approval):* apply that existing alias map
when `poll_refresh.py` builds each row, plus a test. Then republish the poll
snapshot (a published-data change, so it needs your approval). An app-only
alternative is canonical-name matching in the four poll lookups.

### Low-severity observations (none block the beta)

- **L1:** no committed `package-lock.json`, so each Pages build resolves `^` ranges fresh.
  Builds are not reproducible, and the supply-chain exposure is wider than needed.
  The only `npm audit` items are Vite 5.4.21 and esbuild 0.21.5 dev-server
  advisories; they are not present in the shipped static files.
- **L2:** GitHub Pages sends HSTS but no CSP, `X-Frame-Options` or `Referrer-Policy`,
  and the HTML has no CSP meta tag. Risk is low: no accounts, no third-party scripts,
  no user content, and analytics are off until consent. A CSP meta tag is optional
  hardening.
- **L3:** every load logs a console 404 for `v4-program-intelligence.json`. This is
  intentional: the file is deliberately unpublished and the views fall back to
  verified V5 data. It is noise only.
- **L4:** the asset-cache regex in `sw.js` (`\.[a-f0-9]{8,}\.(js|css)$`) never matches
  Vite's names (`index-BYo-bNpD.js`), so the service worker caches no assets. The
  offline page and the "no cached live JSON" contract still work as designed.
  No user impact.
- **L5:** for screen readers, the document title and focus don't change between
  destinations, there are no `aria-live` announcements (for example on scenario
  completion), and there is no skip link (6 Tab stops before content). Semantics
  are otherwise sound: `lang="en"`, one `main`, one `h1`, labelled navigation,
  a visible indicator on all 57 Tab stops, and Enter activates navigation.
- **L6:** the table View/Compare buttons are 37 px tall. That meets WCAG 2.2 AA
  (24 px) but is below the 44 px platform guideline.
- **L7:** re-running an old deploy as a rollback fails once its data is more than
  72 h old, because the staleness gate rejects it. Roll forward instead (§4).
- **L8:** client error telemetry is opt-in only (default off, and GPC/DNT block it).
  Most beta errors will only be seen through feedback issue #27.

### 3.4 Live data audit (Chromium and `curl`, 17:04 UTC)

- **Report:** 138 teams with contiguous, unique ranks; 233 upcoming and 3,453
  completed games; no duplicate schedule IDs; all probabilities finite and within
  [0, 1].
- **Freshness:** `retrieved_at` was 3.3 h old. The scenario packet hash equals the
  live report; the CFP simulation used 10,000 draws; the bracket has 12 seeds.
  Model status is `incumbent_not_v3_promoted` and the challenger is
  `authorized: false`.
- **Schedules:** no FBS game is shown as upcoming after its kickoff. 33 non-FBS
  (D2/D3/NAIA) predictions remain in the JSON after kickoff because CFBD never
  marked them final. The UI filters predictions to upcoming FBS schedule games,
  so fans don't see them.
- **Texas Tech:** model #10, 9–1, after the Nov 15 refresh; official CFP #12
  (Nov 10 release, week 11); AP/Coaches week 11.
- **Live vs. checked-in report:** the live `season-report.json` is identical to
  `data/season-2026-report.json` apart from `generated_at`.
- **Records:** all 138 published W–L records match an independent recomputation
  from the raw snapshot with aliases resolved. All 718 FBS-vs-FBS games are in
  the schedule.
- **Predictions:** predicted winner, margin sign and probability agree for all
  233. CFP national-title probabilities sum to 1.000 and field probabilities to
  12.000.
- **Polls:** AP, Coaches and CFP each have ranks 1–25 exactly once. The only
  unmatched names are `Miami` in AP and Coaches (D4).

## 4. Operational readiness

- **Hosting:** static GitHub Pages behind Fastly. It is suitable for 25–50 users.
  Loopback load tests up to 50 visitors passed in PR #29 (not a CDN capacity claim).
- **Monitoring:** the GitHub email on a failed workflow run, the deploy-time live
  smoke test, and the in-app stale banner after 72 h. There is no uptime or error
  alerting.
- **Incident response (proposed):**
  1. Triage issue #27 daily during the beta.
  2. For wrong data: compare the in-app "Last successful data check" time with the
     latest `Refresh CFBD season snapshot` commit.
  3. If a bad snapshot is live, revert that data commit on `main` (do not touch
     `data/pregame-2026-history.json` entries newer than the revert). The Pages
     workflow redeploys automatically and its validations rerun.
  4. For an app regression, revert the merge commit on `main` with current data
     kept (roll forward). Do not re-run an old deploy (L7).
  5. Note the incident in issue #27.

## 5. Physical-device and human testing required

No physical-device result exists. All Android/PWA evidence is Chrome emulation,
and nothing at all covers iOS Safari. Automated or AI interaction is not a
substitute for first-time-user testing.

**Before invites (about 15 minutes per device): one real iPhone (Safari) and one
real Android phone (Chrome).**

1. Open the live URL; Home loads; the data time is shown.
2. Rankings → open Texas Tech → step through all four Profile sections.
3. Compare Texas Tech with Georgia; predictions load.
4. Playoffs → Explore scenarios → pick a winner → results change → Reset restores them.
5. Save a favorite, close the browser, reopen: the favorite persists.
6. Add to Home Screen; launch it standalone; turn on airplane mode → the offline
   page appears; turn it off → the app recovers.
7. Menu → About & privacy: the feedback link opens; Usage analytics defaults to Off.
8. Enlarge system text: nothing is clipped. If possible, try VoiceOver or TalkBack
   across the main destinations.

Record the device, OS and browser versions in issue #27.

**During the beta:** treat the first 5–10 fans as the usability cohort.
- Ask them to complete three tasks without help: find Texas Tech's next-game
  prediction; compare Texas Tech with a rival; run one playoff what-if.
- Note any confusion about model rank versus AP/CFP rank, and whether they
  understand it is a snapshot, not live scores.

## 6. Prioritized recommendations and decision

1. **Condition 1 — before invites:** complete the §5 physical iPhone and Android
   checklist with no blocking failures. This closes the largest unknown
   (WebKit/iOS).
2. **Condition 2 — before invites:** either approve the D1 refresh-regression
   guard, or accept D1 for the beta with a manual check after each game day:
   Texas Tech's record and the completed-game count look right. Use the §4
   rollback if not.
3. Recommended before invites: the D4 poll-name alias fix, so a top-5 team
   doesn't show as Unranked.
4. Recommended, not blocking: the D2 table focusability markup; mentioning in the
   invitation that data refreshes a few times a day (D3).
5. **Pending, waiting for computer access:** Firefox and WebKit automated runs;
   the §5 physical-device checklist; screen-reader spot checks; PostHog project
   privacy settings and private dashboard; the first-cohort usability session.
6. Later, optional: commit a lockfile (L1); add a CSP meta tag (L2); title, focus
   and live-region announcements (L5).

**Final recommendation: CONDITIONAL GO for the initial 25–50 Texas Tech fan beta.**
No Critical defect was found. Game data, records, predictions, privacy behaviour
and Chromium journeys verify correctly. The one display-accuracy defect is D4
(Miami's AP and Coaches rank). The beta becomes a full GO once conditions 1 and 2
are met; the D4 fix is strongly recommended alongside them. Firefox and WebKit
are pending, not failed. No code was changed, nothing was merged or deployed, and Version 6
remains closed.
