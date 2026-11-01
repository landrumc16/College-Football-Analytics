# Version 1.0 release gates

Status: **IN PROGRESS**. A successful GitHub Pages deployment alone is not a complete release sign-off.

## Required evidence

- [x] Mobile-first navigation and responsive dashboard implementation committed.
- [x] Predictions, rankings, conference analysis, CFP forecast, schedules, and what-if views implemented.
- [x] Published-data source, timestamp, demo/stale warnings implemented.
- [x] Genuine archived pregame forecast accuracy and Brier scoring implemented, with zero-sample disclosure.
- [x] Backend tests for archived forecast accuracy and validation added.
- [x] Confirm latest main commit passes Python tests, TypeScript build, report validation, and Pages deployment. Evidence: run 41341132284, commit 05d406a; 94 tests passed, build and deploy successful.
- [ ] Confirm the next successful CFBD refresh publishes `prediction_accuracy` and timestamp to the live season report.
- [ ] Verify all six dashboard sections on phone-size viewports, including scrolling, selects, tables and loading/error states.
- [x] Verify published Pages HTML, assets, and season-report.json load after deployment. Evidence: run 41341132284 deploy smoke test succeeded, including the production JavaScript entrypoint and historical backtest JSON.
- [x] Compare selected frozen-baseline metrics with the source Google Sheet; document discrepancies and tolerances. Evidence: run 41341132284 strict numerical parity diagnostic reported 0 metrics exceeding 0.001. This does not establish full coverage of every sheet formula.
- [ ] Audit official CFP qualification/seeding rules and identify any deliberate model approximations in user-facing methodology.
- [ ] Validate an archived pregame forecast becomes eligible only after its corresponding game is completed, and no hindsight forecasts are included.
- [ ] Reconcile README and handoff with actual implemented features and verified workflows.

## Release criteria

Release Version 1.0 only when all gates above have recorded evidence. Never claim prediction accuracy with zero archived completed games. Do not retire the Google Sheet until parity is verified. A failing deploy or stale live data blocks release.

## Next work batch

1. Verify a successful live refresh run and resulting published report; frozen demo success is not sufficient.
2. Complete mobile viewport and CFP rules checks, then release documentation.
3. Tag v1.0.0 only after remaining gates have evidence.
