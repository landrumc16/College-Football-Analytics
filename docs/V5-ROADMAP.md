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

## Execution focus decision — November 9, 2026
- Owner approved a streamlined finish-first approach: prioritize completing M1/M5 public usability and integrated experience, then publish M2/M3 historical comparisons for a meaningful independently supported coverage set, without pursuing exhaustive optional school/year coverage.
- Stop adding speculative verification infrastructure or repeated micro-improvements. Run targeted checks for changed behavior, then comprehensive release-candidate acceptance.
- Keep all definitive V5 acceptance requirements intact: no invented historical records or pregame forecasts, no unsupported publication, no unapproved challenger promotion, and no production merge without explicit owner approval.
- If a core historical or archived-forecast requirement lacks genuine evidence, document the exact source/evidence blocker and decision needed instead of presenting missing results as complete.
- Next engineering pass: prioritize end-to-end product integration and browser usability over further evaluator enhancements; then acquire/verify the minimum meaningful historical coverage and archived forecasts required for publication.

## Finish-first execution procedure — owner-approved November 9, 2026

This procedure governs *how* V5 work is executed; it does not replace or weaken the six milestones or Definitive V5 Definition of Finished above.

1. **Resume, don't restart.** Read AGENTS.md, this roadmap, current branch HEAD and the last recorded checkpoint. Inspect only files relevant to the next incomplete acceptance criterion. Do not recreate plans or repeatedly audit settled work.
2. **Finish user-visible paths first.** Complete M1 and M5 onboarding, favorites, freshness/error handling, navigation, shared Team Profile/Programs/Compare behavior, mobile usability, and PWA functionality using the working V4 implementation. Preserve the incumbent prediction engine and V4 production.
3. **Research a bounded meaningful set.** Reuse historical source inventory and existing calculations. Select and document a meaningful set of programs with independent, season-specific strength and preseason/final poll evidence; verify 3/5/10-year windows and publication cutoffs. Publish supported historical results only; show missing values honestly. Do not require exhaustive optional coverage, but do not waive the core historical publication requirement.
4. **Finish forecast reporting from authentic archives.** Reuse the current evaluator and incumbent forecasts. Only score independently established pre-kickoff snapshots against finalized outcomes. Provide sample sizes, coverage, accuracy, Brier, log loss and calibration. Do not present retrospective model results as archived forecasts or promote a challenger.
5. **Build in substantial vertical slices.** Each pass should deliver a complete user-facing workflow or coherent research-to-display integration, with related tests and a focused commit. Avoid isolated micro-commits, new infrastructure, cosmetic redesign and speculative features. Make routine engineering decisions without interrupting the owner.
6. **Test the changed behavior immediately.** Run targeted Python/TypeScript/browser checks for each slice and fix confirmed failures. Do not keep rerunning unchanged passing suites. CI status visibility is not a substitute for actual local/browser acceptance; if the GitHub Actions interface cannot expose a run, use a runnable checkout or record the specific unavailable evidence instead of building more verification machinery.
7. **Freeze and validate once.** After M1–M5 functionality and source evidence satisfy their acceptance criteria, freeze the exact candidate SHA; run the complete Python, historical integrity, prediction/CFP, TS/build, Chromium, PWA, refresh and navigation checks. Inspect actual screenshots at 375, 390, 768 and 1536px. Fix blockers and rerun affected tests; record exact evidence.
8. **Enforce the release gate.** Do not claim V5 complete, source authenticity, forecast performance, CI success or production readiness without evidence. If a mandatory requirement is genuinely blocked by unavailable historical or archived-forecast data, record exactly what is missing, the minimum evidence required, and the owner decision needed; do not silently remove it. Prepare one final approval report only after the definitive acceptance criteria pass. Never merge or modify main without explicit owner authorization; after approval, deploy, inspect live product, record production SHA and formally close V5.
9. **Compact handoff after interruptions.** Record exact development SHA, complete user-visible changes, tests actually run, remaining mandatory blocker, and the next concrete engineering action in this existing roadmap. Do not generate a new roadmap or new version.

**Working priority:** finish public experience and cross-page integration -> establish bounded independently reviewed historical coverage -> integrate verified program intelligence -> publish genuinely archived forecast evaluation -> complete full candidate acceptance -> request merge authorization.

## Execution checkpoint — November 9, 2026 (integration pass)
- Development branch latest feature/test commit before checkpoint: `33c5f67dcc526ed401f9e46e0a2c2778b0fac438`; production `main` remains protected.
- Completed source changes: dedicated Compare Teams view with incumbent-model rank, strength, record, projected wins and CFP qualification odds; direct comparison entry from favorites, Rankings and Program Intelligence; Team Profile navigation from favorites, rankings, programs and comparison. Existing model calculations and missing-value disclosure retained.
- Added/updated browser acceptance scripts for comparison and program/favorites drill-through, official CFP poll publication date, and historical table columns. **These are committed but have not been run on the latest candidate; do not mark acceptance passed.**
- Blocking evidence remains: independently reviewed historical season-strength/preseason/final-poll source records sufficient for meaningful 3/5/10-year publication; authentic timestamped pre-kickoff forecast archive with finalized outcomes; full candidate TypeScript/build, Python, Chromium, PWA and screenshot verification. Neither historical nor forecast authenticity can be inferred from retrospective data.
- Next concrete action: obtain a runnable checkout of the exact development SHA and execute `web` TypeScript/build plus Chromium smoke to repair any failures, then independently review bounded historical source records and genuine forecast archive before release-candidate acceptance. Do not add more evaluator infrastructure or merge main.

## Owner-approved completion focus — November 9, 2026 (supersedes earlier execution priorities, not acceptance criteria)

**Decision:** V5 remains the final scope. The application is substantially implemented but not release-accepted. Stop incremental navigation/polish commits unless a reproduced defect blocks a required journey. Finish the outstanding evidence and acceptance work in **three consolidated passes**. The six milestones M1–M6 and the Definitive V5 Definition of Finished above remain mandatory and unchanged.

### Completion pass 1 — Historical intelligence, research through publication (M2/M3)
- Use existing 2016–2025 source-retrieval, integrity, retrospective season-rating, and poll research assets before fetching anything new. Retrieve actual GitHub Actions historical artifacts or execute the existing workflow from a runnable checkout; record source URLs, season coverage, checksums, independent review and publication cutoffs. A workflow configuration or retrospective Elo diagnostic is **not** itself a publication approval.
- Select a **bounded, meaningful documented set of programs** for which season-specific strength and genuine preseason/final AP and Coaches evidence can be independently verified. Produce reproducible 3/5/10-year trajectories, Hype Index and cross-program comparisons only where the required observations exist. Record missing seasons, poll absence, comparability limits and coverage denominators. Never substitute current rankings or retrospective predictions for historical source records.
- Publish only source-attested outputs through the existing historical publication gate, then verify the actual Hype, Trajectory, Programs, Team Profile and Compare screens agree. Do not wait for exhaustive optional school coverage.
- **Pass exit:** versioned publication artifact + documented covered programs/years/sources + passing relevant integrity/parity checks + real user-facing results; otherwise name the exact missing source and owner decision required.

### Completion pass 2 — Authentic prediction evaluation, research through display (M4)
- Preserve the incumbent V4 prediction engine. Locate existing frozen pre-kickoff forecast snapshots (including archived workflow artifacts and previous immutable publications) and independently match them to verified final results. Do not manufacture timestamps or re-run the model on historical results and call them pregame predictions.
- Reuse the existing evaluator to publish reproducible accuracy, Brier, log loss, calibration, sample sizes, confidence segments, coverage and only properly paired baseline comparisons. Show unavailable metrics when no genuine archive exists; that disclosure is honest but **does not satisfy** the mandatory archived-forecast acceptance requirement.
- Confirm matchup explanations and CFP outlook reflect the actual incumbent inputs, with targeted prediction/CFP checks and browser verification.
- **Pass exit:** traceable archive + reproducible scored report + integrated, understandable public reporting; otherwise identify the exact archive gap and request a specific scope/evidence decision instead of adding evaluator infrastructure.

### Completion pass 3 — Freeze, end-to-end acceptance, release decision (M1/M5/M6)
- Fix only reproduced, release-blocking integration defects. Verify onboarding, isolated persistent favorites, search, This Week, Rankings, Programs, Team Profiles, Compare, schedules, predictions, playoffs, privacy, freshness/failure states and PWA against a **single frozen development SHA**.
- Run the existing full Python, historical integrity, forecast, CFP, TypeScript, production build, browser, mobile, PWA and data-refresh suites. Inspect **actual screenshots** at 375px, 390px, 768px and 1536px; record tested SHA, commands, outputs, workflow links and remaining limitations. Rerun affected checks after a fix; do not claim success from code review or an unobserved workflow.
- **Pass exit:** all definitive V5 gates pass, no release-blocking defects, source coverage/research limitations and release notes documented, and one final approval report prepared. Request explicit owner authorization **before** any merge. Keep `main` unchanged until approval.

### Anti-stall enforcement and evidence checkpoint
- Each pass is one coherent research-to-user-facing outcome, not a succession of cosmetic micro-commits. Reuse existing tests and workflows; no new roadmap, version, redesign, or speculative verification framework.
- When tooling cannot retrieve a runnable checkout, workflow artifacts, or browser evidence, record that **specific capability blocker** and the shortest available recovery path. Do not silently substitute code inspection for executed acceptance or spend additional passes polishing unrelated screens.
- If genuine historical poll/strength evidence or immutable pregame forecasts cannot be recovered, **stop that blocked acceptance claim** and present the exact minimum evidence and narrowly scoped owner decision. Do not weaken the Definitive Definition of Finished without explicit owner direction.
- **Checkpoint before this amendment:** development HEAD `8ae1c490abb477d27dcbfd1c9318257be6c44ab1`; navigation and CFP-table isolation changes committed, but latest TypeScript/build/Chromium/screenshots not executed; no verified historical publication artifact or authentic scored pregame archive demonstrated. This amendment changes execution focus only, not acceptance status.
- **Immediate next action:** retrieve and independently inspect existing historical workflow artifacts or run the established ten-season pipeline, identify a publishable bounded program cohort, and complete pass 1. Do not resume unrelated UI improvements.
