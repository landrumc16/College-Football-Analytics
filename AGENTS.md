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

## Current task — Version 6 visual and editorial polish

The owner authorized a focused refinement on `v6-editorial-polish` from main
`70191e42df15f932733843df801a54de04847319`. Improve hierarchy, typography,
spacing and fan-facing wording within the existing pages. Preserve the approved
logo/palette/serifs, navigation and mobile bottom bar, all functionality, source
limits and accessibility. Do not change engine/data/calculations/simulation,
favorites/PWA contracts or dependencies. No new version or unrelated feature.
Capture comparable real-build before/after screenshots using the same real data,
verify all five viewports and existing Python/browser/PWA regressions, and deliver
a finished PR plus concise visual comparison. Do not merge without owner approval.

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
