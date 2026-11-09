# College Football Analytics — Version 5.0 Authoritative Roadmap

**Repository:** `landrumc16/College-Football-Analytics`
**Development:** `v5-development`
**Production:** `main` (V4 baseline `26672c4ae5e7a965706cffce246aff27075fcc47`)
**Status:** Approved planning baseline; implementation and acceptance not yet complete.
**Release:** One V5 release after explicit owner approval. Do not alter production before approval.

## Product objective
Deliver a dependable, accessible public college football intelligence product answering: How good is a team now? Is its program improving over 3/5/10 years? Is it outperforming documented expectations? How does it compare with other programs? What is likely to happen next and how reliable are the forecasts?

Extend V4; do not rebuild it. Preserve rankings, conference comparisons, weekly predictions, schedules, CFP forecasts, This Week, favorite teams, school search/autocomplete, PWA, mobile navigation, automated updates, and incumbent prediction engine.

## Operating rules
1. Think before coding; simplicity first; surgical changes; reuse working systems; verify meaningful behavior (Karpathy principles).
2. Execution over discussion. Work in consolidated, substantial passes; no repeated roadmap creation, audits of unchanged passing work, cosmetic churn, or speculative features.
3. Review `AGENTS.md`, existing V4 release gate, historical research assets, CI, and code before implementation. Actual GitHub state is authoritative.
4. Keep `main` untouched until explicit merge approval. Work on `v5-development`; use focused commits and record milestones.
5. Use source-attested data; never invent missing rankings, preseason expectations, recruiting effects, historical classifications, or prediction gains. Never leak future information into historical calculations.
6. Reuse shared metric functions across Program Intelligence and Team Profiles. Keep the incumbent model authoritative; a challenger is optional and requires separately approved promotion.
7. Each milestone finishes only when its functionality, tests, documentation, and user-visible behavior pass. Do not equate code committed with completion.
8. Missing optional coverage is nonblocking only if the agreed core capability is genuinely delivered for a documented meaningful coverage set; otherwise identify a blocker and request a scope decision.
9. Run targeted tests during development, full final-candidate acceptance once; rerun affected checks after changes. Stop when release definition is met.

## M1 — Public product foundation
**Build:** First-visit onboarding; independently persisted up-to-three favorites per device; honest no-cross-device-sync explanation; accessible data timestamps, freshness/stale/error states; About, methodology, privacy, and actionable feedback channel; operational failure detection/notification; PWA install/update/offline handling; clear forecast uncertainty; mobile accessibility. Do not require accounts for public beta.
**Finished when:**
- New users can navigate without instructions; returning users are not obstructed.
- Favorites survive app restart and remain independent across browser profiles; storage limitations are disclosed.
- Sources, update timestamps, stale and unavailable states are understandable and correct.
- Refresh failures are detectable and surfaced; feedback channel is usable; privacy/methodology accessible.
- Android PWA and desktop browser journeys pass; all V4 core regression tests pass.
**Evidence:** Browser journeys, screenshots, refresh/failure test, PWA tests, documented operational checks.

## M2 — Historical research foundation
**Build:** Inventory existing repo/Sheet research once; coverage by team, season, source, and metric; canonical team identity/conference changes; reproducible historical team-season records (results, schedule strength, poll snapshots, recruiting only where independently attested); 3/5/10-year windows; preseason-to-final comparisons; provenance, cutoffs, missing-data policy, validation and versioned artifacts.
**Finished when:**
- Coverage inventory and source contracts are documented.
- School identities, season windows, duplicate detection, and no-future-data cutoffs pass tests.
- Preseason ranks are sourced independently, not inferred from final polls.
- Supported 3/5/10-year analyses run reproducibly for a meaningful documented program coverage set; limitations explicitly identified.
- Recruiting/expectations results publish only with independent evidence; unsupported values are unavailable.
- Data artifacts and integrity tests are reproducible without repeated redundant downloads.
**Evidence:** Source inventory, coverage report, historical integrity tests, reproducible generated outputs.
**Boundary:** Missing optional schools/years may be disclosed. Missing evidence for the core promised historical capability is a blocker, not a reason to fabricate or silently drop the requirement.

## M3 — Advanced Program Intelligence
**Build:** Integrate supported 3/5/10-year Program Trajectory; evidence-backed preseason expectations/Hype Index; Stock Watch with explicit observation window and no fabricated stock score; Contenders/Pretenders explained through current strength, résumé and incumbent CFP odds; supported recruiting versus results; historical program comparisons. Consolidate into Program Intelligence and shared Team Profile calculations, not redundant pages.
**Finished when:**
- National/conference filtering, search, sorting, and team drill-through work.
- Verified historical trajectory and expectations appear only for supported coverage.
- Short-term form, current strength, and long-term direction are never conflated.
- Program Intelligence and Team Profile agree on shared metrics.
- Missing values are honestly explained; desktop/mobile acceptance and regression tests pass.
**Evidence:** Calculation fixtures, provenance gates, cross-page parity tests, screenshots and browser journeys.

## M4 — Prediction and matchup intelligence
**Build:** Clear winner probability, margin, confidence and matchup explanations grounded in actual incumbent model inputs; archived pregame forecasts vs outcomes; accuracy, Brier, log loss, calibration, coverage, sample sizes, baseline comparisons and meaningful segment breakdowns; preserve CFP and conference outlook. Optional challenger remains separate.
**Finished when:**
- No hindsight forecasts contaminate accuracy reporting; sample sizes and coverage are clear.
- Metrics and baseline comparisons reproduce from archived forecasts.
- Explanation statements are consistent with actual model behavior.
- CFP and prediction regression tests pass; no unapproved challenger is promoted.
**Challenger promotion gate (separate approval):** >=5% pooled Brier improvement; >=3 of 4 held-out seasons; <=2% log-loss regression; favorable 95% clustered confidence interval; no leakage; acceptable calibration and coverage.
**Evidence:** Frozen backtests, provenance and accuracy reports, tests and browser checks.

## M5 — Integrated user experience
**Build:** This Week remains immediately useful; easy Rankings, My Teams, Programs, Compare, Playoffs; existing predictions/schedules/research accessible; consolidated Team Profile; two-school comparisons from shared metrics; historical, poll, recruiting, outlook context only where verified; detailed methodology separated from casual overview; preserve established branding.
**Finished when:**
- Users reach Team Profile from search, rankings, Programs, and comparisons.
- Two-school comparisons and Team Profiles are consistent and understandable.
- Search autocomplete, favorites, schedules, rankings, predictions, CFP, PWA and navigation remain functional.
- Real browser tests at 375px, 390x844, 768px and 1536x900 show readable layouts without blocking overflow.
- Accessibility and important navigation journeys pass; redundant placeholder experiences are eliminated.
**Evidence:** Integration/browser tests, accessibility checks, inspected real screenshots.

## M6 — Final validation and release
**Build:** Freeze candidate; full Python/model, historical integrity, research, prediction, CFP, frontend TS/build, browser, mobile, PWA, refresh and operational validation; inspect actual screenshots; document sources/coverage, release notes, exact tested SHA and workflow links; request owner approval; only then merge and verify live deployment.
**Finished when:**
- All M1–M5 required acceptance gates are satisfied; no material unresolved release blockers.
- All required automated checks pass on the same final candidate; changes trigger affected revalidation.
- Desktop/mobile screenshots and meaningful browser behavior are actually inspected.
- Release notes, historical limitations, data provenance, exact candidate SHA and acceptance evidence are documented.
- Owner explicitly approves merge; PR merges into `main`; GitHub Pages deployment and live essential journeys are verified; production SHA recorded; V5 formally closed.
**Evidence:** Final release gate, CI links, visual/browser evidence, approved PR, production deployment and smoke-test results.

## Definitive V5 definition of finished
V5 is complete ONLY when:
1. A first-time fan can use the public product without guidance and understands data freshness, methodology and uncertainty.
2. Personal favorites persist independently on a device; limitations and privacy are disclosed.
3. Verified 3/5/10-year trajectories and historical expectations are published for a documented meaningful coverage set, with honest gaps and no fabricated metrics.
4. Current form, program development, strength, and performance versus expectations are clearly distinguished.
5. National, conference, team search, sorting, Team Profile and side-by-side program comparison work and share consistent calculations.
6. Archived forecasts yield reproducible accuracy/calibration/coverage reporting and honest explanations.
7. The incumbent prediction engine, CFP simulations, schedules, rankings, This Week, favorites, PWA, and automated updates remain operational.
8. Production builds, Python tests, historical/data checks, browser integration, desktop/mobile and PWA checks pass on the exact release candidate.
9. Real screenshots are inspected and no verified release-blocking defects remain.
10. Provenance, limitations, release notes, test evidence, exact SHA and production approval are recorded.
11. The owner explicitly authorizes the merge; deployment, published data and essential live behavior are verified; V5 is closed.

## Execution order and handoff
Begin M1 implementation and M2 inventory in parallel without blocking public readiness on speculative data acquisition. Then complete M2 -> M3 -> M4 -> M5 -> M6. Keep a compact milestone status and exact next action in this file or existing project tracking documentation; do not spawn new roadmaps. If interrupted, record exact commit, verified results, outstanding blocker, and next action. Never claim completion from workflow success alone.

## Execution checkpoint — November 9, 2026
- Development HEAD before this note: `ef31e704b736a07d2e314684ec8721769ced235c`. Production remains at the V4 baseline; no release authorization.
- M1 implementation in progress: public onboarding, local-only favorites/privacy disclosure, GitHub feedback link, browser-profile isolation test, and recoverable report-fetch error with a retry browser test. Existing freshness, PWA and incumbent model code are preserved.
- M1 acceptance remains open: full frontend build, real Chromium journeys/screenshots, PWA update/install checks, and operational alert evidence are not yet verified on this branch. No GitHub workflow run was returned for the preceding development commits; no pass is claimed.
- M2 existing assets identified: `v4_team_season_records.py`, `v4_coverage_summary.py`, `v4_program_provenance.py`, `v4_program_intelligence_cli.py`, `v4_program_trajectory.py`, and the existing historical source checks. Reuse these; do not rebuild or infer unsupported preseason rankings.
- M2 evidence blocker: the V4 Program Intelligence release gate explicitly records that no independently source-reviewed `web/public/v4-program-intelligence.json` is published. The CLI requires full ten-season strength and poll coverage plus independent source review before publishing. Historical 3/5/10-year trajectory and Hype Index must remain unavailable until real verified source inputs satisfy that gate.
- Next action: validate the M1 implementation on a runnable candidate and run the existing historical coverage/provenance tools against available verified assets. Publish historical intelligence only after source authenticity and required coverage are independently established. Then proceed to M3–M6 without weakening gates.
