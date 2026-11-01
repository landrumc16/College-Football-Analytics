# Version 1.0 release gates

Status: **TECHNICAL AND VISUAL GATES VERIFIED** against workflow run 41345784302 and user visual review. Final release tagging remains outstanding.

## Required evidence

- [x] Mobile-first navigation and responsive dashboard implementation committed.
- [x] Predictions, rankings, conference analysis, CFP forecast, schedules, and what-if views implemented.
- [x] Published-data source, timestamp, demo/stale warnings implemented.
- [x] Genuine archived pregame forecast accuracy and Brier scoring implemented, with zero-sample disclosure.
- [x] Backend tests for archived forecast accuracy and validation added.
- [x] Confirm release-candidate code passes Python tests, TypeScript build, report validation, and Pages deployment. Evidence: [run 41345784302](https://github.com/landrumc16/College-Football-Analytics/actions/runs/41345784302), build and deploy jobs successful, including live-site smoke. Subsequent documentation-only commits require separate HEAD verification before tagging.
- [x] Confirm CFBD refresh writes `prediction_accuracy` and timestamp to the live season report. Evidence: refresh commit 22b9e5a, snapshot and report retrieved_at 2026-11-01T17:10:33Z; source collegefootballdata.com/games; 138 teams and 842 upcoming predictions. The previously reported 20-game accuracy sample was invalid for FBS-only evaluation and must **not** be cited as verified accuracy. Separately verify Pages serves the newly rebuilt live report.
- [x] Verify all six dashboard sections on phone-size viewports. Evidence: run 41345784302 mobile Playwright smoke passed at 375px, 390px, 768px, checking section navigation, key rendered content/controls, page-wide overflow and unavailable-report state; screenshots retained as CI artifact. User reviewed the live dashboard and approved its appearance. Detailed manual interaction of every table is not independently established.
- [x] Verify published Pages HTML, assets, and season-report.json load after deployment. Evidence: run 41341132284 deploy smoke test succeeded, including the production JavaScript entrypoint and historical backtest JSON.
- [x] Compare selected frozen-baseline metrics with the source Google Sheet; document discrepancies and tolerances. Evidence: run 41341132284 strict numerical parity diagnostic reported 0 metrics exceeding 0.001. This does not establish full coverage of every sheet formula.
- [x] Audit implemented CFP selection/seeding assumptions and disclose approximations. Code review: `cfp.py` and `pipeline.py` model five highest-scored conference champions plus seven at-large, seed all 12 by model score, award top four byes, and simulate neutral-site title games. Conference-specific qualification/tiebreakers and committee decisions are intentionally omitted and identified in both report methodology and README. Official-rule equivalence has **not** been established; recheck if rules change.
- [x] Validate end-to-end archived pregame eligibility in CI. Implemented: ingestion retains `start_date`; report archiving requires a completed FBS matchup and source retrieval **and forecast generation** before kickoff; accuracy and performance scoring exclude unverified archive entries. Regression tests added in `tests/test_pregame_timestamps.py` and `tests/test_pregame_scoring.py`. Existing archived history without verified kickoff evidence remains excluded. Run 41345784302 build job passed with these regression tests in the test suite.
- [x] Reconcile README with implemented features and verified workflows. Evidence: commit 051ef3c documents run 41341132284, live refresh provenance, retrospective-versus-prospective accuracy, and remaining limitations. Handoff remains historical context.

## Release criteria

Release Version 1.0 only when all gates above have recorded evidence. Never claim prediction accuracy with zero archived completed games. Do not retire the Google Sheet until parity is verified. A failing deploy or stale live data blocks release.

## Next work batch

1. Confirm documentation-only release changes do not alter the verified application and verify the final HEAD workflow.
2. Record release version and create the v1.0.0 tag using a supported GitHub release/tag mechanism.
3. Begin Version 2 planning separately; do not expand Version 1 scope.
