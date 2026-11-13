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


## 2026-11-13 first independent in-repository reconciliation

Compared the retained `data/pregame-2026-history.json` forecast ledger against completed, scored fixtures in the committed `data/season-2026-report.json` schedule by exact game ID, home/away names, chronological `source_retrieved_at <= forecast_recorded_at < scheduled_kickoff_at`, and `source=generated_before_kickoff`. This **preliminary broad match** finds **58** Week 10 games, **36** correct, winner accuracy **0.6206897**, Brier **0.2188375**, log loss **0.6275879**. The committed scorecard has **57** games, **35** correct, accuracy **0.614**, Brier **0.2227**, log loss **0.6385**.

**Do not replace the published scorecard with the 58-game numbers.** The broad reconciliation has **not** yet applied the production `eligible_teams` FBS universe, provider alias rules, duplicate/conflicting completed-result exclusion, or all `_has_verified_pregame_provenance` checks. A one-game difference may therefore be an intended FBS exclusion; the precise cause is **not yet established**. Next run the existing `build_prediction_accuracy` against the original game snapshot and eligible FBS roster, identify the excluded game ID, and require an exact 57-game reconciliation before treating the archived scorecard as independently reproduced. This is a bounded discrepancy, not evidence of fabricated results.


## 2026-11-13 discrepancy resolution — exact scorecard reproduction

The 58th preliminary match was **Wake Forest vs Merrimack**, game ID `401858290`, Week 10. Merrimack is an FCS opponent, so this fixture is ineligible for the production **FBS-vs-FBS** accuracy scope. Excluding this single game from the retained forecast ledger and committed completed-game schedule produces **57 games, 35 correct winners, accuracy 0.6140350877, Brier 0.2226765933, log loss 0.6385431864**. These round exactly to the committed scorecard: **0.614, 0.2227, 0.6385**. This resolves the 58-versus-57 discrepancy without changing the model or reported metrics.

Reproduction selection: exact game ID, identical home and away team names, completed game with non-tied numeric scores, forecast source `generated_before_kickoff`, and `source_retrieved_at <= forecast_recorded_at < scheduled_kickoff_at`; exclude the Wake Forest–Merrimack FCS game from FBS-vs-FBS. This checks the **committed November 9 snapshot**, not an independent second provider or newly refreshed 2026 results. The other historical and full browser/PWA release gates remain open.
