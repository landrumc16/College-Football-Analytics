# AI-assisted development rules

Use these rules for all implementation and review work in this repository.

## Think before coding
- Inspect relevant existing code, contracts, and tests before editing.
- State assumptions only when they matter; resolve uncertainty with evidence.
- Identify the smallest complete feature boundary and its verification criteria.

## Simplicity first
- Prefer direct, readable Python/TypeScript over clever abstractions.
- Reuse existing model functions and data types; do not duplicate business logic.
- Avoid speculative architecture, dependencies, and premature optimization.

## Surgical changes
- Keep changes scoped to the current deliverable.
- Preserve working behavior, interfaces, fixtures, and historical baseline.
- Fix underlying causes rather than weakening tests or hiding errors.

## Verify
- Run targeted tests and the full suite when feasible.
- Report what was actually run, what passed, and what remains unverified.
- Never claim CI, API refresh, spreadsheet parity, or production readiness without evidence.
- Do not commit API keys, credentials, or private data.

## Ship substantial increments
- Prioritize an end-to-end usable product over paperwork and micro-refinements.
- Group related implementation, tests, and integration into meaningful chunks.
- Make routine engineering decisions without interrupting for minor approvals.
- Document only decisions, setup, and operational details needed to maintain or use the system.

## Public beta readiness — GO and formally closed (2026-11-14)

The owner approved data-only PR #28 at
`3b41d327c9a713f00113f720cd598f39c58d7653`. All required checks passed;
it merged/deployed as `2c47bec5935fd32844ef20c307e3aab4c201d052`.
The live November 10 CFP comparison matches all 25 reviewed official positions,
including Texas Tech #12. Existing numeric outputs match the prior deployment
exactly. Five-width live journeys and Android Chrome-emulated PWA acceptance
passed. No beta readiness holds remain; GO for the initial 25–50 Texas Tech fans.
See `docs/PUBLIC-BETA-READINESS.md` and its retained receipt for final evidence.
Feedback issue #27 remains open for real-user reports. Version 6 stays closed;
no new version, feature, redesign, model promotion or development cycle is
started or authorized by this closeout.

## Version 6 visual/editorial refinement — released and closed (2026-11-14)

The owner approved PR #26 at `2c0bc1b50733272a1d5b76b755b652f1083c97e3`,
conditional on passing checks. Every required check passed before merge.
It merged and deployed as `195fbd143df002b733a4f36e6030b5677a9f19d4`.
Actual production browser acceptance passed at 375/390/430/768/1536px,
including rankings, profiles, program intelligence, comparisons, predictions,
research, favorites, scenario output/exact reset and Android Chrome-emulated
PWA installation/update/offline/recovery. The approved refinements are live;
the incumbent remains authoritative and the challenger was not promoted.
See `docs/V6-PRODUCTION-ACCEPTANCE.md` and
`docs/evidence/v6-editorial-production-2026-11-14.json` for final evidence.

Version 6, including this refinement, is formally closed. No new feature or
version is authorized. The next owner-stated objective is preparing the existing
application for a small public beta with Texas Tech football fans; this closeout
does not initiate another development cycle. Preserve the released design,
analytics, verified archive, source limits, favorites and PWA contracts.

## Version 6.0 — released and closed (2026-11-14)

The owner approved PR #25 at `6bcaa3a649ff781d81906e7f11e468cf3abb23a9`
after visual review. It merged as `60e5c8b762dfaab5f29c2e88389f3516f8edb61e`.
Production acceptance passed at `fda1fc284a6214611eeae4451d67daaea722d670`,
including the deployment-only packet staging correction. See
`docs/V6-PRODUCTION-ACCEPTANCE.md` and its retained machine-readable receipt.
All approved milestones, production deployment, live five-width browser journeys
and Android Chromium-emulated PWA checks are complete. Version 6 is closed.

The incumbent remains authoritative; the challenger was not promoted. Preserve
the V5/V6 design, navigation, functionality, verified archive, source provenance,
favorites and PWA freshness contract. Raw restricted source corpora stay private.
Do not reopen completed development, begin another version or add unrelated
features without a new owner instruction. Separate explicit owner approval is
still required for any challenger promotion.

## Navigation consolidation — completed and closed (2026-11-13)

The owner approved PR #18 at `e7ea35d439bc51d97d63ba6f74d16de3ffe41a97`.
It merged and deployed as `34d12e3a6819caf17f1dc58bf60b0dc8ba35b5f1`.
The five primary destinations, four Profile sections and preserved Version 5
features passed production browser and Android Chrome PWA emulation checks.
See `docs/UX-NAVIGATION.md` for exact deployment and live acceptance evidence.

This refinement and Version 5.0 are closed. No implementation work remains
under these directives. Do not begin another version, add unrelated features,
or change production without a new explicit owner instruction. Preserve the
incumbent engine, calculations, methodology, verified archive and working app.

## Historical V5 finish-first execution rules (2026-11-10)
The authoritative scope and release gate are in `docs/V5-ROADMAP.md`, including the
approved Program Report Card amendment. V4 features and the incumbent prediction
engine must remain intact. Work only on `v5-development`; never change or merge
`main` without explicit owner approval.

### Definition of a development pass
- Deliver an **end-to-end user-visible feature or a resolved release blocker**:
  implementation + real-data integration + tests actually executed + applicable UI
  verification. A module, test file, workflow, or commit alone is not a deliverable.
- Work through dependent tasks within the same pass. Do not stop to report after
  each commit. Prefer one cohesive commit for each complete feature when practical.
- First complete national-source-gated Report Card publication across Programs,
  Hype, Trajectory, Team Profile and Compare; then authentic archived-forecast
  evaluation; then full regression, browser, PWA and screenshot acceptance.
- Reuse existing historical research artifacts and V4 ratings. Do not build a new
  strength model or replace the prediction engine. Do not add new versions, new
  roadmaps, speculative abstractions, or cosmetic work outside a release blocker.

### Evidence and blocker discipline
- Before starting research, inspect existing artifacts and the specific missing
  evidence. Attempt one reasonable recovery for a genuinely missing source,
  record its exact limitation, and continue independent executable work. Do not
  repeatedly retry the same unavailable source or manufacture verification.
- Historical grades require reviewed eligible-FBS peer coverage, source provenance,
  and the approved equal-weight scoring contract. Missing grades remain N/A.
- Retrospective forecast calculations must never be labeled authentic archived
  pregame predictions. A missing genuine archive remains a release blocker.
- Run targeted tests immediately after implementation; run full Python, TypeScript
  production build, browser navigation, persistence/PWA, and 375/390/768/1536px
  screenshot acceptance before freezing an RC. Never report unexecuted tests as passed.
- If execution is genuinely blocked by environment/tool access, identify the
  exact command, error, missing artifact or authorization; do not imply completion.

### Reporting and stopping rules
- Report completed functionality, actual test evidence, exact branch SHA, and
  remaining genuine blockers only. No activity-based progress summaries.
- Continue through the approved deliverables rather than stopping at a commit.
- Request merge approval **only after** all pre-merge acceptance gates pass and a
  consolidated release-candidate report with the exact tested SHA is ready.
