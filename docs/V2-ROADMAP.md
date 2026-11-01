# Version 2.0 roadmap — Prediction Quality and Model Validation

Status: APPROVED PLANNING BASELINE (implementation not started). Version 1.0 functionality is frozen pending formal GitHub tag/release.

## Objective
Improve *measured out-of-sample* FBS game prediction quality, calibration, and explanatory transparency while retaining the six-section mobile dashboard. No accuracy claims without verifiable pregame inputs and a declared sample.

## Non-negotiable principles
- Keep V1 frozen as the comparison baseline; tag v1.0.0 before merging V2 model changes.
- Prevent look-ahead leakage. Archive forecasts with timestamps and evaluate only against games that began afterward.
- Separate retrospective walk-forward backtests from live prospective results; report sample size, winner accuracy, Brier score, log loss, and calibration.
- Include FCS opponent results in FBS team strength and schedule analysis where valid; do not silently treat FBS–FCS games as eligible FBS-vs-FBS prediction accuracy.
- Audit source Google Sheet formulas before changing equivalent calculations; retain documented parity tolerances.
- Prefer simple, testable improvements and explicit ablations over complex unexplained models.
- Ship in large, independently testable increments; avoid speculative UI redesign and new dependencies unless justified.

## Milestone 1 — Data integrity and reproducible evaluation
- Inventory V1 inputs, original Google Sheet formulas, source timestamps, missing data, FCS effects, ranking logic and forecast eligibility.
- Define a canonical historical dataset and provenance contract for multiple seasons, with source versions and missingness flags.
- Implement chronological, season-aware walk-forward validation with frozen baselines and reproducible evaluation reports.
- Acceptance: deterministic reruns; leakage tests; V1-vs-V2 baseline scorecard; clear FBS/FCS treatment.

## Milestone 2 — Ranking and game prediction research
- Evaluate opponent-adjusted team strength, home-field effects, recency, strength of schedule, and preseason-prior decay.
- Test candidate models one factor at a time against the V1 baseline and compare across seasons, conferences and forecast horizons.
- Calibrate win probabilities and quantify uncertainty; avoid optimizing only winner pick rate.
- Acceptance: documented out-of-sample improvement or explicit rejection of candidate; no degraded calibration concealed by aggregate accuracy.

## Milestone 3 — Forecast and CFP realism
- Propagate calibrated game probabilities through remaining schedules and conference championship scenarios.
- Validate conference standings/tiebreaker assumptions and CFP selection/seeding rules against the applicable season rules; disclose committee uncertainty.
- Compare forecast stability, scenario sensitivity, and simulation convergence against V1.
- Acceptance: reproducible simulation tests and transparent approximations.

## Milestone 4 — Trustworthy comparisons and explanations
- Automate verified AP and Coaches Poll snapshots where permitted, and show poll-vs-model differences with poll dates.
- Add concise explanations of major rating moves, prediction drivers, confidence, and data freshness.
- Retain the existing mobile-first navigation and six core sections; add only high-value displays.
- Acceptance: mobile/browser smoke, source traceability and usable explanations without dashboard clutter.

## Milestone 5 — Operational hardening and V2 release
- Automated data refresh, historical regression suite, model drift monitoring, stale-data safeguards and reproducible model artifacts.
- Shadow-run V2 beside V1 before switching the published default.
- Final acceptance: multi-season walk-forward evidence, prospective sample clearly separated, passing CI/Pages/mobile checks, updated methodology and explicit v2.0.0 release gates.

## Scope boundaries
- No unsupported guarantees of betting profitability or future win rate.
- No rewriting the dashboard or replacing the existing pipeline solely for novelty.
- No new model promoted merely because it fits the same historical data it was tuned on.

## Execution order
1. Complete V1 GitHub release/tag and verify final HEAD.
2. Implement Milestone 1, then run the baseline before model changes.
3. Progress through Milestones 2–5, with evidence-based go/no-go decisions.
