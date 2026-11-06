# College Football Analytics — Version 4.0 Roadmap
## Theme: Proven Predictive Intelligence, Not Feature Volume
**Status:** APPROVED FOR DEVELOPMENT — NOT RELEASED
**Branch:** `v4-development`
**Production baseline:** V3.4.2 on `main`; validated dashboard deployment [42169215432](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42169215432), application SHA `e76ea2ef35ad6d03171476efc95caf780642b9f9`.
**Primary objective:** deliver a materially better, independently validated prediction and college football intelligence system. No promotion on cosmetic improvement alone.

## 1. Product definition — what a finished V4 looks like
A fan opens the familiar, fast, mobile-first This Week dashboard, sees meaningful win probabilities, rankings, CFP outlooks and games that matter, and can open any prediction to understand the **evidence-backed reasons**: demonstrated team performance, talent and roster continuity, coaching context and opponent-specific strengths, with missing data explicitly disclosed. The model is demonstrably better calibrated and more useful than the incumbent across held-out historical seasons and prospective archived games. A separate Research & Data view explains the datasets, tests, limitations, and comparisons. V3 functionality remains intact.

The upgrade is not a complete UI rebuild, a replacement for the existing Google Sheet, or a promise to predict winners perfectly. New features and model inputs are admitted only when they add validated value.

## 2. Non-negotiable quantitative release gates
1. **Predeclared primary metric:** mean out-of-sample Brier score for pregame winner probabilities; lower is better. Use identical eligible FBS-game cohorts and prediction cutoffs for incumbent and challenger, and compare to a simple preseason/reference baseline. Log loss is a mandatory corroborating metric; winner accuracy, calibration by probability bin, coverage, and upset performance are reported, not optimized in isolation.
2. **Material gain:** target at least **5% relative Brier-score reduction** against the frozen incumbent on a pooled, strictly held-out multi-season evaluation. Also require positive Brier improvement in **at least 3 of 4** distinct held-out season folds, with no material log-loss regression (greater than 2% relative). These are explicit product release targets, not a forecast of achievable improvement.
3. **Uncertainty and sample integrity:** report per-season sample counts, 95% confidence interval for the paired Brier difference using game-week or team-season clustered resampling, and a transparent sensitivity analysis. Require the interval to favor V4 (upper bound of V4-minus-incumbent Brier < 0) before claiming statistically supported superiority. If data volume or leakage prevents a credible test, do not claim the target was met.
4. **Prospective reality check:** preserve immutable pre-kickoff prediction snapshots with timestamps, model/version/data-as-of IDs and final results; report 2026 prospective performance separately from retrospective backtests. Do not invent prospective records or retroactively reconstruct them as if archived.
5. **No cherry-picking:** report all eligible FBS games, including FBS–FCS matchups under a consistent documented policy; segment by FBS-only vs FBS–FCS, favorites/upsets, conference, season and probability band. Handle missing/forfeited/canceled games transparently. No selective removal of difficult games.
6. **No future leakage:** each historical example must use only roster, transfer, coaching, recruiting, ratings and results known by its pregame cutoff; document publication and availability dates. Use rolling-origin / walk-forward validation and keep test folds untouched during feature selection.
7. **Integrity and reliability:** existing tests and new leakage/identity/calibration/CFP regression tests pass; Python tests, frontend typecheck/build, mobile browser smoke, and published-site smoke pass on the actual release commit. CI cannot promote a challenger without explicit evaluation evidence and approval.
8. **Production acceptance:** `main` release deployed to GitHub Pages, actual commit and published data verified, desktop/mobile user journeys checked, release notes and final evidence ledger committed, owner acceptance recorded. No automatic model promotion.

**Decision rule:** If the material gain cannot be proven, keep V3.4.2's model in production. A research-only V4 candidate is not a completed V4.0 product; document the negative result and stop or revise the scope rather than weakening the gates.

## 3. Work packages — execute in large, testable chunks

### M1 — Frozen baseline and evaluation contract
- Inventory actual incumbent model, historical backtest, archived pregame forecasts, spreadsheet parity checks, source schemas, and scheduled refresh pipeline.
- Freeze baseline model code/version, evaluation datasets, eligibility and cutoff rules; save reproducible baseline Brier/log loss/accuracy/coverage per season.
- Establish challenger-vs-incumbent paired comparison runner, provenance and evaluation report schema; make historical versus genuinely prospective records unmistakable.
- **Exit:** reproducible baseline and deterministic evaluation tests; gaps documented, no fabricated archive.

### M2 — Time-aware historical data foundation
- Assemble versioned season/week/team records for historical scores, team stats, recruiting classes, coaching staffs and coordinators, transfers, returning production and roster experience when available.
- Normalize school identities and conference membership by season; preserve FBS/FCS policy, game venue, dates, data source and as-of availability.
- Audit coverage and licensing/API constraints; prioritize reliable datasets over speculative proxies. Fall back gracefully where history is incomplete.
- **Exit:** reproducible dataset manifests, completeness tables, no-leakage checks and stable data contracts across held-out years.

### M3 — Coaching, roster and talent intelligence
- Evaluate head-coach track record, coordinator history, staff continuity and scheme tendencies using only pregame evidence.
- Test recruiting quality, talent development versus recruiting expectation, transfer inflow/outflow, returning production and experience as separate ablations.
- Exclude or label weakly sourced factors; keep explainability tied to measured model inputs.
- **Exit:** per-factor ablation report including gain, coverage, uncertainty and maintenance cost; retain only useful factors.

### M4 — Opponent-specific matchup model
- Develop parsimonious offense/defense matchup features, tempo and efficiency interactions, home/away/neutral venue, and opponent-adjusted strengths where supported.
- Use one prediction pipeline with explicit baseline/challenger selection; no competing production models, no hidden manual overrides.
- Calibrate probabilities on training/validation data only; prevent CFP/rankings/head-to-head from using incompatible assumptions.
- **Exit:** deterministic end-to-end challenger predictions and grounded 'Why this pick?' explanations.

### M5 — Independent historical and prospective validation
- Perform walk-forward multi-season holdouts; paired Brier/log-loss comparison, calibration and coverage; inspect error concentrations and negative cases.
- Compare against baseline, incumbent, and simple ablations; produce 95% clustered uncertainty and sensitivity results.
- Continue recording real pregame 2026 snapshots and evaluating only after final scores. Do not wait for the entire season to begin research, but do not treat retrospective predictions as prospective.
- **Exit:** signed-off promotion decision against Section 2; stop if gains are not material and robust.

### M6 — Meaningful fan-facing V4 experience
- Keep the proven four-section This Week layout and favorite teams; add concise evidence-backed prediction drivers and matchup advantages only when supported.
- Surface model confidence, freshness, verified coaching/talent/roster context and meaningful uncertainty without overwhelming the main page.
- Improve CFP and rankings only insofar as the validated challenger changes their inputs; official CFP poll data remains separately sourced, dated, and honestly unavailable when missing.
- Put deeper methodology, per-factor evidence and backtests on Research & Data; preserve search autocomplete, poll comparisons, FBS/FCS, PWA and sharing.
- **Exit:** user can identify what is new, why a prediction changed and what evidence supports it; mobile smoke and accessibility checks pass.

### M7 — Production verification and release
- Freeze scope; run full Python, TypeScript/build, UI/browser, dataset provenance, historical model, CFP simulation and deployment checks.
- Merge only the validated candidate and approved UI changes; verify `main` deployment and published artifact hashes/commit.
- Commit V4 release notes, evidence ledger, actual gains and limitations; obtain owner acceptance; mark roadmap COMPLETE only afterward.
- **Exit:** all Section 2 gates passed and V4.0 is deployed, independently checked and formally closed.

## 4. Explicit exclusions and engineering rules
- No wholesale rewrite, new dashboard framework, unnecessary microservices, parallel data pipelines, or speculative player-level scouting scores.
- No paid data dependency without a documented affordable alternative and explicit approval; no API secrets in source control.
- No invented coaching/transfer/roster history, unsupported predictive claims, or future information in backtests.
- No AP/Coaches poll substitutions for official CFP committee rankings; preserve verified date/source safeguards.
- Use Karpathy principles: understand before coding; reuse existing modules; smallest coherent changes; clean, readable and maintainable code; verify behavior before expanding.
- Work in substantial milestones, not repeated tiny tweak cycles. Don't reopen settled V3.4.2 work or change `main` before a verified release decision.
- Preserve the original Google Sheet as numerical reference, without editing it.

## 5. Release decision and contingency
**GO** only if the 5% relative Brier improvement, cross-season robustness, non-regressing log loss, uncertainty test, provenance safeguards, user-facing value, and deployment gates are all satisfied.
**NO-GO** if any mandatory gate fails. Preserve V3.4.2 in production and publish a research outcome; do not rename an incremental or unproven model V4.0.
**Review checkpoint:** After M2, confirm historical data coverage is sufficient for four honest held-out season folds. If not, revise the evaluation design openly before looking at test outcomes, rather than inventing data or relaxing thresholds afterward.
