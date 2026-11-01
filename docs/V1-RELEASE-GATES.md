# Version 1.0 release gates

Status: **IN PROGRESS**. A successful GitHub Pages deployment alone is not a complete release sign-off.

## Required evidence

- [x] Mobile-first navigation and responsive dashboard implementation committed.
- [x] Predictions, rankings, conference analysis, CFP forecast, schedules, and what-if views implemented.
- [x] Published-data source, timestamp, demo/stale warnings implemented.
- [x] Genuine archived pregame forecast accuracy and Brier scoring implemented, with zero-sample disclosure.
- [x] Backend tests for archived forecast accuracy and validation added.
- [ ] Confirm latest main commit passes Python tests, TypeScript build, report validation, and Pages deployment.
- [ ] Confirm the next successful CFBD refresh publishes `prediction_accuracy` and timestamp to the live season report.
- [ ] Verify all six dashboard sections on phone-size viewports, including scrolling, selects, tables and loading/error states.
- [ ] Verify published Pages HTML, assets, and season-report.json load after deployment.
- [ ] Compare team ratings, ranking order, and selected probabilities with the source Google Sheet; document discrepancies and tolerances.
- [ ] Audit official CFP qualification/seeding rules and identify any deliberate model approximations in user-facing methodology.
- [ ] Validate an archived pregame forecast becomes eligible only after its corresponding game is completed, and no hindsight forecasts are included.
- [ ] Reconcile README and handoff with actual implemented features and verified workflows.

## Release criteria

Release Version 1.0 only when all gates above have recorded evidence. Never claim prediction accuracy with zero archived completed games. Do not retire the Google Sheet until parity is verified. A failing deploy or stale live data blocks release.

## Next work batch

1. Check current workflow result and fix any CI failure.
2. Execute data-refresh integration and verify published accuracy.
3. Complete sheet parity and mobile smoke checks.
4. Update README, capture verified run IDs and tag v1.0.0.
