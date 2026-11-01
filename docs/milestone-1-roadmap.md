# Milestone 1 — Spreadsheet-to-Python Model Parity

**Status:** In progress. **Source of truth:** [2026 Google Sheet](https://docs.google.com/spreadsheets/d/1kpCF_5_BNQx43IywvwpUra5-o6kcdMZBHwed1pDVJ54/edit). **Rule:** do not modify the workbook or declare parity before comparing all model outputs.

## Objective
Reproduce the existing spreadsheet's college-football rating, ranking and game-prediction calculations in a deterministic, tested Python package. Preserve the current model before proposing improvements.

## Workstream A — Baseline inventory and frozen fixtures
- [x] Confirm workbook and its 26 tabs.
- [x] Identify key tabs: Teams, Games, PreseasonPrior, Model Settings, Rankings, Predictions, Top 25.
- [x] Inspect representative live formulas and settings.
- [ ] Export all 138 FBS team rows (inputs and reference outputs), completed game rows, preseason priors, model settings, rankings and predictions into versioned, sanitized test fixtures.
- [ ] Inventory all named ranges and formulas, including remaining-schedule/projected-wins rank key, all iterative Games contribution columns, and neutral-site handling.
- [ ] Inspect Apps Script source and recent weeklyUpdate executions if access is provided. Do not infer a confirmed root cause from stale results alone.
- [ ] Record workbook date, game count, maximum week and fixture hashes.

## Workstream B — Python engine
- [x] Create package skeleton, settings, basic probability/margin/prior helpers.
- [ ] Port opponent-adjusted iterative team ratings and conference shrink (all active passes).
- [ ] Implement adaptive selection of rating iterations based on completed-game thresholds.
- [ ] Port strength of schedule, quality wins, bad losses and resume calculations.
- [x] Implement blended rank-score calculation from projected wins and rating (Teams!AW).\n- [x] Implement remaining-schedule projected wins, win variance and conference-win expectation.\n- [ ] Verify projected wins, rank key, Top 25 and all-team ordering against full workbook baseline.
- [x] Implement game prediction functions with neutral-site home advantage and separate market/model probability paths; full-sheet parity pending.
- [ ] Preserve FCS fallback behavior and handle missing/duplicate/neutral/tied games.

## Workstream C — Verification and operational readiness
- [x] Add initial pytest unit tests for primitive calculations.
- [ ] Build end-to-end parity tests against frozen Sheets reference data; publish a discrepancy report by team and game.\n- [x] Add initial ranking and prediction unit tests.
- [ ] Require exact win/loss/game counts, matching ranking order (with documented tie policy), and numeric tolerances for ratings/probabilities.
- [ ] Run full tests in GitHub Actions on push and pull requests.
- [ ] Add a CLI that produces local rankings and predictions from frozen fixtures, without API credentials.
- [ ] Write a reproducible setup guide and milestone closeout report with test output, limitations and next milestone handoff.

## Acceptance criteria
1. A clean checkout can install and execute the model and tests without secrets or Google Sheets access.
2. Every reference team/game has an explicit reconciliation result; no unexplained discrepancies.
3. The model matches the frozen baseline for ratings, rank keys, ranks, and prediction probabilities to documented tolerances.
4. Data freshness is surfaced separately from formula correctness.
5. The original Google Sheet is unchanged and remains usable during migration.
6. CI passes; a full, reproducible parity report and next-milestone handoff are committed.

## Execution guidance
Work in large, integrated increments: (1) export/port rating engine; (2) projected rankings and prediction parity; (3) CI, CLI, reconciliation and closeout. Do not block progress on cosmetic design or deployment.

## Known baseline facts
As inspected on 2026-10-31, Top 25 reported **Week 7 · 510 games**. The sheet calculates ratings; the weekly update script is referenced in Season Checklist but its execution history is not yet verified. The workbook currently uses ridge strength 5, conference shrink 1, margin cap 45, win probability scale 18, prior-year weight 1, FCS rating -26, home-field advantage 3 and market scale 19.5. These are **observed workbook values**, not newly endorsed parameters.

## Risks
- The full iterative model spans many formula columns and must be transcribed exactly.
- The workbook mixes betting-market and model-only probabilities; preserve both.
- A stale or failed CFBD ingestion script is a separate operational issue, scheduled for Milestone 2 after diagnosis.
- Existing prose in the workbook may disagree with formulas; live formulas and effective values govern parity.
