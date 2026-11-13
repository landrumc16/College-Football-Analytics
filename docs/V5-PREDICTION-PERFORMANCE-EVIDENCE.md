# V5 prediction-performance evidence — 2026-11-13 checkpoint

## Existing scored pregame results (not a full-season claim)

The committed `data/season-2026-report.json` (season 2026, generated `2026-11-09T21:28:51.040893+00:00`, source `collegefootballdata.com/games`) already includes a `prediction_accuracy` scorecard. Do not characterize V5 as lacking *all* scored pregame evidence.

| Metric | Value |
| --- | ---: |
| Evaluation scope | archived_pregame_fbs_vs_fbs |
| Scored games | 57 |
| Correct winners | 35 |
| Winner accuracy | 0.614 |
| Brier score | 0.2227 |
| Log loss | 0.6385 |
| Margin MAE | 13.527 points (57 games) |
| Eligible completed games in snapshot | 562 |
| Forecast coverage | 0.1014 |
| Scored weeks | Week 10 (57 games) |

The scorecard is a **historical snapshot** as of November 9, not a fresh November 13 run. Its internal `data_freshness.status=current` describes the snapshot when generated, not current freshness. Report the denominator and narrow forecast coverage alongside every accuracy claim. Do not extrapolate 61.4% to all completed games or call this a full-season performance result.

## Remaining M4 acceptance work

1. Independently reproduce the 57 matched outcomes from the archived prediction ledger and retained final game records; validate immutable pre-kickoff forecast and source-retrieval timestamps, team/game identity, and outcome finality. Exclude any row that fails, with an explicit reason.
2. Recompute accuracy, Brier, log loss, calibration and confidence segments using the existing `v5_forecast_evaluation.py`; compare to the committed report, documenting differences in selection and rounding.
3. Refresh the existing production data pipeline only through an approved safe branch/release procedure. **Do not dispatch `.github/workflows/refresh-data.yml` from the development branch**, because that workflow pushes to `main`.
4. Verify current-season coverage and display the sample size, scope, retrieval date and limitations in the application. Preserve incumbent V4 forecasts and do not promote a challenger.

This is evidence for finishing V5, **not** a declaration that M4 or the full release acceptance gate has passed.
