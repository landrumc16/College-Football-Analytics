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

## Current priority — V5 finish-first execution (2026-11-10)
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
