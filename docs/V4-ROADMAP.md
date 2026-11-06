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

## 6. Approved additional V4 capabilities — integrated scope (November 2026)
These additions strengthen the existing M1–M7 plan, not a new development cycle or excuse for indefinite scope growth. Prioritize measurable accuracy gain and genuinely useful fan-facing explanations. Do not delay release for unavailable or unproven data.

### A. Opponent-adjusted schedule strength and quality of wins — ESSENTIAL
- Distinguish raw offensive/defensive production from opponent-adjusted performance, including strength of schedule, quality of wins/losses, and opponent-adjusted efficiency.
- Avoid circular rankings, double-counting opponent strength, and future results in historical pregame estimates. Evaluate separately from existing strength-of-schedule inputs to avoid redundant features.
- **Milestones:** M2 source/availability schema; M4 model ablation; M5 holdout test; M6 concise strength-of-opposition explanation.

### B. Recent form, improvement and decline — ESSENTIAL
- Test rolling, time-decayed pregame trends for team efficiency, offense/defense performance and consistency, with preseason shrinkage to avoid overreacting to small samples.
- Model season-to-season and within-season changes without treating postgame or end-of-season data as pregame knowledge. Distinguish genuine improvement from weak recent opponents.
- **Milestones:** M2 dated game features; M4 candidate model; M5 ablations and calibration; M6 evidence-backed trend indicator.

### C. Availability and injuries — HIGH, SOURCE-CONDITIONAL
- Assess the feasibility of trustworthy timestamped injury/availability and quarterback-status data. If coverage is sparse or inconsistent, omit from production rather than fabricate player-level ratings or backfill postgame injury reports.
- Require explicit missing-data behavior, publication cutoff checks, and tests for whether availability materially improves forecasts. Never make private health inferences.
- **Milestones:** M2 feasibility/coverage decision; M3 isolated ablation if supported; M6 explanation only for verified source-backed signals.

### D. Uncertainty, upset risk and calibration — ESSENTIAL
- Show calibrated win probability and explain uncertainty using evidence-backed data coverage, model disagreement or empirically validated uncertainty measures; do not equate a 55% win probability with a guarantee or invent precise confidence intervals.
- Evaluate underdog calibration, high-confidence errors, uncertainty buckets, and late-season drift; flag when missing roster or source data limits the estimate.
- **Milestones:** M1 evaluation definitions; M4 calibration; M5 reliability/coverage analysis; M6 readable confidence and upset explanations.

### E. Explainable forecast movement — HIGH
- Archive versioned, timestamped weekly model outputs; compare rankings, game probabilities and CFP odds to prior *genuinely archived* snapshots and explain changes with supported inputs (results, opponent-adjusted form, schedule, roster updates).
- Keep model-version changes separate from football changes; if the prior snapshot is missing, show 'movement unavailable' rather than synthetic historical deltas.
- **Milestones:** M1 snapshot contract; M2 storage and provenance; M5 replay tests; M6 'What changed?' research/detail views.

### F. Scenario-based season and CFP forecasting — HIGH
- Reuse the existing 10,000-season Monte Carlo and venue-aware matchup machinery to evaluate clearly labeled, conditional what-if outcomes (e.g. if a team wins a selected upcoming game), without building a second simulation engine.
- Maintain correct season-specific CFP qualification/seeding constraints, conference scenarios and reproducible simulation seeds. Distinguish hypothetical results from real forecasts; avoid claims of exact committee decisions.
- **Milestones:** M4 shared model interfaces; M5 consistency/regression checks; M6 lightweight scenario exploration on a detail page, not an overloaded homepage.

### G. Optional independent market benchmark — RESEARCH ONLY
- If legally usable, properly timestamped historical pregame odds are available at reasonable cost, derive no-vig market probabilities as an external comparison benchmark. Report cohort alignment and source limitations. Do not use future closing lines for earlier forecast cutoffs or silently train on market odds.
- This is not a betting feature, pick service, gambling recommendation, or mandatory release dependency. No-go on unsupported or expensive sources.
- **Milestones:** M1 benchmark contract; M2 feasibility; M5 separate comparison if available.

### H. Data-quality and model-drift monitoring — ESSENTIAL OPERATIONAL SAFEGUARD
- Add checks for stale/missing inputs, abrupt distribution shifts, team-ID mismatches, incomplete schedules and prediction coverage. Preserve last validated production data on refresh failure.
- Report model performance drift by week/season with minimum-sample thresholds; alerts must not claim degradation without enough data. Keep scheduled automation simple and reuse existing GitHub workflows.
- **Milestones:** M2 quality contract; M5 monitoring checks; M7 deployment/refresh-failure regression.

### Additional V4 user-value acceptance criteria
- A typical fan can distinguish a strong opponent-adjusted performance from inflated raw statistics and see a sourced, comprehensible reason behind a matchup prediction.
- A fan can see whether a team is trending upward or downward, with sample-size and opponent-quality context.
- A fan can see meaningful probability uncertainty and verified week-to-week movement without invented numbers.
- A fan can explore at least one upcoming-game conditional playoff/conference scenario using the existing simulation engine, with reproducible outputs and clearly hypothetical labels.
- Injury/availability signals and independent market benchmarking are included only if provenance and out-of-sample value justify them; their absence does not block the release.
- No new factor or feature may degrade the mandatory Section 2 model promotion criteria. V4 must remain understandable, mobile-first and maintainable.

### Scope discipline and sequencing
Implement A, B, D and H as core model/operations improvements; E and F as the major new fan-facing differentiators. Treat C and G as feasibility-gated optional work. Fold all into M1–M7, in large verified chunks, without introducing an M8, parallel pipelines or a new release number. The Section 2 quantitative gates and V3.4.2 production protection remain unchanged.
