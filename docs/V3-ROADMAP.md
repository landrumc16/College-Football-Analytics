# Version 3 — Maximum Practical Predictive Accuracy

Status: Approved design standard; implementation not yet started.
Predecessor: V2 Research Beta production deployment verified in Actions run 41372590890.

## Product objective

Build the most accurate college-football prediction and forecasting system reasonably achievable **without getting trapped in diminishing returns**. Prefer measurable out-of-sample gains, maintainability, trustworthy data, and a finished usable product over theoretical perfection.

## Nonnegotiable rules

1. Accuracy over model novelty. Test Elo, opponent-adjusted efficiency, statistical methods, and ensembles as candidates; do not assume any wins.
2. Leakage-free evaluation. Use chronological, season-separated walk-forward tests with only inputs genuinely available before each kickoff. Keep retrospective results distinct from archived pregame forecasts.
3. Score probability quality (Brier score, log loss, calibration), winner accuracy, and margin error; report sample sizes and season-by-season results. Compare on the **same games**, including a simple baseline.
4. Keep FBS-vs-FCS games in strength estimation where appropriate; evaluate FBS-vs-FBS and FBS-vs-FCS outcomes separately. Document data gaps and assumptions.
5. Promotion requires repeatable out-of-sample improvement that justifies added complexity, runtime, and maintenance. No evidence means no promotion.
6. Time-box research and bundle experiments. Do not extend a milestone for speculative marginal gains. Preserve existing working production behavior and rollback paths.
7. Maintain a responsive, explainable dashboard; explanations should reflect actual model inputs and should not imply causal certainty.
8. Treat playoff simulations and committee selection approximations as distinct from single-game model quality. Validate each separately.
9. Keep the original Google Sheet as a reference, not as verified historical truth. Never represent reconstructed forecasts as genuine archived pregame predictions.
10. Complete the full release: tests, data provenance, browser smoke, production deployment, and published-artifact verification.

## Decision policy

- Meaningful, stable out-of-sample improvement with acceptable complexity: adopt.
- Small improvement at negligible cost: consider; document uncertainty.
- Tiny or inconsistent improvement with substantial complexity: reject or defer.
- No measurable improvement: stop that experiment.
- Once acceptance gates pass: ship and move to the next milestone, even if theoretical improvements remain.

Use predefined evaluation metrics, consistent game populations, multiple seasons, and uncertainty checks. Avoid optimizing repeatedly against a held-out final evaluation set. Do not set an arbitrary universal percentage improvement threshold without evidence.

## Milestone sequence

### M1 — Benchmark and evaluation framework
Reproduce the V2 baseline; inventory data provenance and existing model features; build chronological matched-game candidate evaluation and calibration reports; establish a locked holdout and documented acceptance criteria. No production model replacement.

### M2 — Bounded prediction research
Run one consolidated batch of practical candidates: opponent-adjusted team strength, situational factors with verified timestamps, and parsimonious ensembles. Compare to V2 and select the simplest reliably strong candidate. Stop when returns diminish.

### M3 — Production prediction integration
Integrate the selected model into game predictions, team ratings, and schedule projections with feature/version metadata, deterministic tests, fallback, and regression protection. No invented pregame history.

### M4 — CFP and rankings validation
Improve conference-title and playoff forecast fidelity where supported by rules and data. Compare AP, Coaches, and CFP poll snapshots only when verified. Validate ranking behavior and scenario outputs separately.

### M5 — Team intelligence and accountability
Expose useful matchup explanations, model-vs-poll differences, archived pregame forecast tracking, calibration, and errors. Keep the UI mobile-first and avoid dashboard sprawl.

### M6 — Automated release
Automate repeatable weekly data refresh, diagnostics, report generation, frontend smoke, CI and production deployment verification. Publish known limitations and close the V3 release gate.

## Execution discipline

Work in substantial independently testable chunks, not micro-approvals. Keep a concise status/handoff record. Prefer simple, surgical, maintainable changes; no rewrites without demonstrated need. Ask for human input only on a material product decision. Do not hold up the rest of V3 for low-yield optimization.

## V3 release gates

- Historical evaluation is reproducible, leakage-checked, and transparently scoped.
- Any promoted model meets the documented matched-game evidence and reliability bar.
- Forecasts and rankings are appropriately qualified; FCS and CFP caveats remain visible.
- Full regression, frontend build, mobile browser smoke, deployment and published-data integrity checks pass.
- No unverified accuracy or market-outperformance claims.
