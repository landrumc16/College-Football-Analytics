# College Football Analytics — Version 6.0 Authoritative Roadmap
**Status:** Owner-approved product direction; planning PR, not yet implementation or release.
**Repository:** landrumc16/College-Football-Analytics
**Baseline:** current released main; preserve V5 functionality and UX.
**Development:** create v6-development from latest main after planning approval. Never merge without owner approval.

## North star
Version 5 built the platform; Version 6 makes it smarter. Improve verified prediction performance and explain why programs succeed or fail, while preserving a concise sports-publication homepage and detailed drill-down pages. Prediction accuracy is the first priority, not feature volume.

## Operating rules
Read AGENTS.md, V5 roadmap, V5 historical evidence, current code/tests and these V6 documents. Follow simplicity-first, focused, tested engineering. Work in substantial end-to-end passes. Never claim accuracy gains without leak-free held-out evidence. Do not alter V5 production or promote challenger without separate explicit owner approval. Preserve incumbent as fallback. Use source provenance, snapshots and clear unavailable states. Do not re-download already archived historical evidence without cause.

## Milestones and finish gates
### M1 — Verified research foundation
Inventory existing 2016–2025 verified archive, data contracts and gaps. Add provenance-tracked recruiting, transfer/roster continuity and coaching history where source quality and temporal cutoffs permit. Freeze as-of snapshots, school identity crosswalks, licensing/usage terms and coverage tables. Do not imply complete coverage from partial records.
**Done:** reproducible versioned datasets; source URLs/checksums and as-of dates; team-season coverage and missingness reports; duplicate/identity/leakage tests; documented exclusions; data contract used by M2/M3.

### M2 — Prediction intelligence (highest priority)
Establish incumbent frozen out-of-time baseline from genuine timestamped pregame forecasts; develop a minimal challenger only after eligible features are available. Evaluate accuracy, Brier, log loss, calibration, confidence intervals and segment/season stability using chronological folds, pregame-only features and common game samples. Explain matchups only with actual model inputs.
**Done:** reproducible frozen comparison; no leakage; challenger meets every gate in V6-MODEL-EVALUATION.md or remains experimental; incumbent stays authoritative until separate owner promotion approval; UI reports honest uncertainty and sample sizes.

### M3 — Program intelligence
Use verified recruiting, coaching, roster and performance history to describe development versus expectations and reasons for improving/declining programs. Separate correlation from causation; preserve V5 3/5/10-year trajectories, Hype Index, Stock Watch and Report Cards.
**Done:** shared tested calculations across Programs, Team Profile and Compare; transparent drivers, provenance, uncertainty and missing-data indicators; national coverage report; cross-page parity and browser tests.

### M4 — Playoff and conference what-if scenarios
Build scenario overrides atop existing season simulator: user picks plausible future winners, recomputes conference and CFP probabilities with clear assumptions. Avoid implying deterministic playoff committee decisions or exact certainty.
**Done:** coherent scenario constraints, reproducible seeded runs, baseline-vs-scenario comparison, invalid-input handling, simulation performance budget measured on mobile, integration and probability-sanity tests.

### M5 — Personalized game-day experience
Improve favorite-team relevance, game previews, forecast movement and explanatory summaries without clutter. Preserve local favorites privacy and independent per-device storage. Do not require accounts.
**Done:** compact summary-first homepage with deep links, five-destination bottom navigation, accessible secondary dropdowns, favorites persistence, stale-data behavior and verified PWA journeys.

### M6 — Integration, acceptance and release
Freeze release candidate; validate data lineage, predictions, simulation, shared metrics, UI, accessibility, mobile/desktop, PWA, deployment and operations.
**Done:** every required gate in V6-RELEASE-ACCEPTANCE.md passes on one exact candidate SHA; release notes and evidence links published; owner explicitly approves merge; main deployed and live app verified. No release claim before deployment.

## Execution order
M1 and baseline M2 first; M3/M4 can follow in parallel only after data contracts stabilize; M5 integrates completed work; M6 closes release. Track dependencies and blockers, not arbitrary percent complete. No new version or roadmap expansion mid-pass.

## Product boundary
Preserve existing branding, concise homepage previews, five main destinations (Home, Rankings, Teams, Playoffs, Research), mobile bottom navigation, mobile secondary dropdowns, Team Profile, school search, rankings, CFP, historical archive, genuine forecast reporting, PWA and favorites. Avoid new top-level pages and deep tab nesting.

## Definitive definition of finished
V6 is finished only when all six milestone deliverables are implemented, provenance and reproducibility pass, no regressions remain, mobile/desktop screenshots are inspected, challenger promotion decision is documented, all acceptance checks pass, owner approves merge, and production deployment is verified. A challenger that fails its promotion gate may remain research-only if M2's reproducible evaluation and explanatory improvements are delivered; never weaken gates or silently promote it. Document any scope reduction for explicit owner approval.
