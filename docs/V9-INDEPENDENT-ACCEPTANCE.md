# V9 Independent Acceptance (Claude Code)

Branch `v9-development`. Reviewed candidate `eacb515` from ChatGPT Work; corrections committed on top of it. The final
release-candidate SHA is the head of the release pull request. Main and production were not modified, and nothing was
deployed or merged.

## Verdict

**Ready for owner approval, with one owner decision and the conditions below.** All three milestones are implemented,
and their acceptance gates pass in a real Chromium browser at all five widths.

Every PR check passes except `privacy-and-browser`, whose visual-identity guard has no release exception (see Owner
decision). Also outstanding:
- physical-device testing by the owner (`docs/V9-ANDROID-CHECKLIST.md`);
- merging PR #56 first, followed by a one-line guard-test reconciliation on V9.

## Pass A — engineering audit

| Check | Result |
| --- | --- |
| Model code | No file under `src/` changes (models, ratings, simulator and strength code are byte-identical to main) |
| Python regression | 836 passed, 1 skipped (candidate and final head) |
| JS units and typography | 11 unit suites pass; title audit: 43 files, 592 labels, 0 inconsistencies; branded bundle verified |
| Protected-path guard (merge base) | 4 protected files changed, all approved by the V9 manifest |
| Accountability (`scripts/v9_accountability.py`) | First retention per game and model, atomic and never rewritten. Requires source ≤ issued ≤ retained < kickoff. Reuses the strict evaluator; legacy rows need `generated_before_kickoff`; kickoff changes, identity mismatches, non-FBS games, ties and invalid probabilities are excluded. Standard/Momentum enter only through pregame retention, so no replay is labelled authentic. Calibration shows per-bin denominators, null bins and an all-three common-game cohort |
| Current evidence | Official 128 scored of 697 eligible; Standard/Momentum 0 settled; common cohort 0, shown as Unavailable and never zero-filled; 240 retained forecasts |
| Post-merge simulation | V9 merged into current main, then the new refresh steps run offline: 71 dual games regenerated with no CFBD calls, 0 retained forecasts overwritten, 1 strength observation added; full suite 835 passed / 2 skipped on the merged tree |
| Failure isolation | **Fixed:** the V9 retention step could fail the production data refresh. It is now non-blocking, like the dual-projection step. The dashboard V9 hook already degrades to "unavailable" |
| Reliability | V9 does not touch the watcher, keeper or freshness monitor; PR #54 behaviour is unchanged |
| Security and privacy | No new third-party requests; the V9 privacy test (`beta-analytics`) passes with the analytics build. No credentials in code; CI uses only existing secrets |

## Pass B — browser acceptance

Real React review build (`node scripts/v9_preview.mjs`), served locally, Chromium via Playwright. Phone widths use
touch and mobile emulation. **Emulation, not physical devices.**

| Area | Result |
| --- | --- |
| Five widths (375/390/430/768/1536), five destinations | All render with no horizontal overflow and no page errors. Screenshots in `docs/evidence/v9-acceptance/` |
| Journeys at every width | Pass at every width: favorite save, browse Baylor, Home keeps Texas Tech, reload persists; Rankings current level (Texas Tech 23.2); trajectory states that one observation cannot establish a trend; Texas Tech vs Baylor at a neutral site (5.12, 65.8%); Momentum projections; Official calibration with denominators; Standard calibration unavailable; Market inside Research |
| Playoffs scenario | At every width: no mismatch notice; the TCU override changes the table; reset restores it exactly; completed games cannot be overridden |
| Keyboard | 22 distinct tab stops on Home, all with a visible focus ring; navigation and disclosures operate by keyboard |
| Reflow and text size | No overflow at 320 px, or at 200% text size at 390 px, on any destination |
| Accessibility scan (axe-core 4.10, WCAG 2.2 AA) | Home, Rankings and Teams clean. The only finding is `scrollable-region-focusable` on pre-existing tables (Playoffs; Research's "Why We Kept the Current Model"), which production also has. The tables V9 added were fixed |
| Touch targets (24 px minimum) | Only the pre-existing Home favorites "+ Add Team" and "Save Team" controls are below it (as in production). The V9 receipts link was fixed |
| Performance, mobile (4× CPU throttle) | Median of 3: first contentful paint 452 ms, largest contentful paint 828 ms, cumulative layout shift 0, total blocking time 71 ms, 119 KB JavaScript. Playoff override to table about 0.9 s |
| Performance, desktop | First contentful paint 68 ms, largest contentful paint 128 ms, cumulative layout shift 0 |
| Offline app (PWA) runtime | Worker activates and controls the page; only `offline.html` is cached (football JSON is never cached). Offline shows the offline page; online recovers. A new worker shows "App Update Available" and removes the old cache |
| Missing data | V9 evidence, scenario packet or season report missing: explicit unavailable messages and no page errors |

**Existing suites** (CI staging): 16 of 17 pass after realignment, including `mobile-smoke` (deploy gate),
`adversarial-reliability` (34 of 34 scenarios) and `beta-analytics`. `v6-browser` passes every functional step but
exceeds its 3,000 ms 4× CPU budget in this shared container (about 3,600 ms; unchanged main measured about 4,000 ms here
earlier). The simulator is byte-identical to main, so GitHub CI is authoritative for that budget.

## Pass C — defects corrected

1. **Browser suites not updated for V9 (release-blocking).** They expected Market in the bottom navigation and
   pre-Title-Case labels, and had never run on the V9 branch. CI and the production deploy's live `mobile-smoke` and
   PostHog checks would have failed after merge. Selectors now follow V9's deliberate changes; no assertion was removed.
2. **Offense & Defense overflow.** At 375 px the National Leaders "Measure" dropdown overflowed by 8 px, because its
   Title Case option text set its width. It is now constrained to its container.
3. **Accountability tables not keyboard-reachable.** They are now focusable named regions, and the receipts link meets
   the 24 px target size.
4. **Non-blocking evidence retention** in `refresh-data.yml` (see Pass A).
5. **V9 build tests broke every full-suite workflow without the frontend toolchain.** That includes the production data
   refresh's pre-commit validation, so score updates would have stopped after merge. These three tests now skip only
   where the toolchain is absent. `tests.yml` and the V9 foundation workflow set `REQUIRE_WEB_BUILD=1`, so a missing
   toolchain fails there instead.
6. **editorial-polish phase-aware labels:** the released V6 "before" source predates Title Case. Parity assertions are
   unchanged.

## CI on the release PR (#63)

All checks pass on the final head except `privacy-and-browser`:
- **Passing:** `pytest` (2), `python`, `python-tests`, `historical` (2), `historical-replay`, `regression` (V5 browser
  acceptance), `visual` (editorial before/after), `frontend`, `dashboard`, `dashboard-build` (2), `foundation`,
  `research-tests`, `strength-blend-screen`.
- **Skipped as usual:** `refresh-evidence`, `deployment-secret-and-live-capture`.

## `privacy-and-browser`: guard resolved (Option A); size budget needs a decision

**Guard (owner chose Option A, implemented):**
- The visual-identity step now uses the reviewed-manifest mechanism over its exact former 13-path list, evaluated on
  the PR head commit.
- The V9 manifest pins `web/src/style.css` (five pinned files in total).
- New guard tests verify the path list is preserved and that unpinned files, altered content, deletions, additions
  and other branches still fail.
- On CI, the guard now approves exactly the five V9 files. Every privacy and browser step behind it passes, including
  consent and events at five widths with intercepted ingestion, the secret-key rejection, and the browser/PWA
  regressions.

**Remaining failing step: "Compare gzip JavaScript against the current production source".** It compares with a
fixed baseline, production `474c72d` (November 17), with a 10,240-byte limit. Measured with the same build:

| Build | Compressed JS | Versus `474c72d` |
| --- | --- | --- |
| `474c72d` (November 17 production) | 97,734 bytes | — |
| Current main / production `b204bd6` | 115,434 bytes | +17,700, already over the limit through released PRs #47–#54 |
| V9 | 123,162 bytes | +25,428 (V9's own share: +7,728 over current production) |

The step runs only when analytics files change, so main's earlier growth went unnoticed. Its comment records one
earlier re-baseline to the then-current production for the same reason, with the limit unchanged.

I prepared re-baselining it to current production (`b204bd6`) with the 10,240-byte limit unchanged. The session's
safety policy blocked it as a budget change, so it needs explicit owner authorization. Options:
- **(c)** Authorize the re-baseline. V9's 7,728 bytes would pass the unchanged limit.
- **(d)** Accept this one failing budget step for the V9 merge.

## PR #56 and reconciliation (rehearsed locally, nothing pushed)

| | |
| --- | --- |
| PR #56 | Head `edc9598`; one commit; 4 files (`freshness_monitor.py`, its tests, its manifest, the guard test) |
| CI | All required checks green |
| Mergeability | Clean |
| Production urgency | Still churning: 97 dashboard runs since PR #54 (67 cancelled); alert issues #57 (172 comments) and #62 (50, still open) |

**Rehearsal:**
1. Merge PR #56 into a copy of main.
2. Merge V9 into that. `tests/test_protected_guard.py` conflicts in two hunks:
   - the manifest list becomes `["freshness-alert-flapping", "freshness-reliability", "v7-development", "v9-development"]`;
   - both sides' appended tests are kept.
3. Result: full suite 839 passed, 2 skipped; guard and freshness tests 42 of 42.

## Owner decision: device testing (November 26)

The owner accepted the automated device evidence (`docs/V9-DEVICE-TESTING.md`) in place of manual owner testing.
Physical-device testing and iPhone offline-app lifecycle verification are **known limitations, not release
blockers**. The automation is preserved as `web/tests/device-profiles.mjs` and
`.github/workflows/device-profiles.yml`: WebKit iPhone/iPad and Chromium Android profiles, run on web pull requests and
on demand. `docs/V9-ANDROID-CHECKLIST.md` remains optional reference material only.

## Remaining limitations

- **Physical devices:** Android and iPhone not tested; use `docs/V9-ANDROID-CHECKLIST.md`.
- **Pre-existing accessibility:** scrollable Playoffs and research tables are not keyboard-focusable, and the favorites
  controls are under 24 px. Present in production; not introduced by V9.
- **Accountability:** Standard/Momentum metrics remain unavailable until retained forecasts settle naturally.
  Accomplishment ranking, rooting guidance and model promotion stay conditional (roadmap).
- **Preview data:** frozen at November 25; live freshness must be verified after deployment against real events.

## Release sequence, deployment and rollback

1. **Merge PR #56 first.** It is the independent freshness-alert hotfix; it touches only `freshness_monitor.py`, its
   tests and its manifest.
2. **Update V9 from main.** `tests/test_protected_guard.py` will conflict on one line, the manifest head-ref list.
   Include `freshness-alert-flapping`. Rerun CI.
3. **Owner approves the exact release-PR SHA**, then merge. The existing dashboard workflow deploys. Verify:
   - deploy and live checks green;
   - five destinations and favorites;
   - scenario/report identity;
   - V9 evidence published;
   - footer freshness;
   - the next data refresh retains forecasts without errors.
4. **Rollback:** re-run the last good dashboard deployment, or revert the V9 merge through an approved PR. Preserve
   retained forecast and strength archives and newer data; never force-push main.
