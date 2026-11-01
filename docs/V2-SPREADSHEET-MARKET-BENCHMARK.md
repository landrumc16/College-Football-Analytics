# V2 Milestone 2 — Spreadsheet vs market benchmark protocol

## Decision gate
Do not replace the spreadsheet-derived eight-pass model without a repeatable, out-of-sample comparison against the frozen workbook model **and** a timestamped betting-market baseline.

## Same-game evaluation universe
- Match by season, provider game ID, teams and kickoff. Record neutral sites, FBS/FCS classification and source version.
- Compare only completed, non-tied FBS–FBS games with verified **pre-kickoff** predictions for all compared systems.
- Archive the original spreadsheet's formula outputs and the exact as-of-game inputs. A postgame recomputation is **not** a prospective forecast.
- Archive market moneyline implied probabilities (remove bookmaker margin when comparing probabilities) and closing spreads, with provider, capture timestamp and sign convention.
- For score-margin accuracy, require both model-projected margin and closing spread. Report MAE and RMSE. For win probability, report winner accuracy, Brier and log loss. For market spreads, do not substitute spread cover rate for outright winner accuracy.
- Report sample size, exclusions, coverage, calibration, by-season results and paired game-level differences. Never claim betting-market parity from a single aggregate winner rate.
- Compare V1, each candidate V2 model, and market on the **same intersection** of games. Separately report coverage of the full eligible season.
- Use chronological walk-forward data splits, no tuning on test seasons, and ablation tests for each changed factor. Require multi-season consistency or label gains exploratory.

## Work order
1. Freeze and export the original workbook's rating, prediction and margin formulas, settings, and team aliases.
2. Establish season-specific priors, schedules, completed results, FCS opponent classifications, and archived as-of forecasts.
3. Obtain legally usable, timestamped historical odds (moneylines and spreads). If unavailable, publish model-only evaluation with **market comparison pending**, not fabricated odds.
4. Build a paired-scorecard utility that refuses unmatched, unverified or postgame rows.
5. Test eight-pass workbook parity before any model tuning.
6. Only then research opponent adjustment, home field, recency, priors and probability calibration.

## Existing work
The V2 historical scorer and CLI handle verified archived FBS–FBS probability forecasts. They do not yet ingest historical market odds or validate workbook margin parity. These are explicit next tasks, not completed capabilities.
