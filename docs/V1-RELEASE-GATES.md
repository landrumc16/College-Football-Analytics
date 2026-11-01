# Version 1.0 release gates

Status: **IN PROGRESS**. A successful GitHub Pages deployment alone is not a complete release sign-off.

## Required evidence

- [x] Mobile-first navigation and responsive dashboard implementation committed.
- [x] Predictions, rankings, conference analysis, CFP forecast, schedules, and what-if views implemented.
- [x] Published-data source, timestamp, demo/stale warnings implemented.
- [x] Genuine archived pregame forecast accuracy and Brier scoring implemented, with zero-sample disclosure.
- [x] Backend tests for archived forecast accuracy and validation added.
- [ ] Confirm **current HEAD** passes Python tests, TypeScript build, report validation, and Pages deployment. Earlier evidence: run 41341132284, commit 05d406a, passed 94 tests and deployed successfully; it does **not** validate subsequent commits.
- [x] Confirm CFBD refresh writes `prediction_accuracy` and timestamp to the live season report. Evidence: refresh commit 22b9e5a, snapshot and report retrieved_at 2026-11-01T17:10:33Z; source collegefootballdata.com/games; 138 teams and 842 upcoming predictions. The previously reported 20-game accuracy sample was invalid for FBS-only evaluation and must **not** be cited as verified accuracy. Separately verify Pages serves the newly rebuilt live report.
- [ ] Verify all six dashboard sections on phone-size viewports, including scrolling, selects, tables and loading/error states.
- [x] Verify published Pages HTML, assets, and season-report.json load after deployment. Evidence: run 41341132284 deploy smoke test succeeded, including the production JavaScript entrypoint and historical backtest JSON.
- [x] Compare selected frozen-baseline metrics with the source Google Sheet; document discrepancies and tolerances. Evidence: run 41341132284 strict numerical parity diagnostic reported 0 metrics exceeding 0.001. This does not establish full coverage of every sheet formula.
- [x] Audit implemented CFP selection/seeding assumptions and disclose approximations. Code review: `cfp.py` and `pipeline.py` model five highest-scored conference champions plus seven at-large, seed all 12 by model score, award top four byes, and simulate neutral-site title games. Conference-specific qualification/tiebreakers and committee decisions are intentionally omitted and identified in both report methodology and README. Official-rule equivalence has **not** been established; recheck if rules change.
- [ ] Validate end-to-end archived pregame eligibility in CI. Implemented: ingestion retains `start_date`; report archiving requires a completed FBS matchup and source retrieval **and forecast generation** before kickoff; accuracy and performance scoring exclude unverified archive entries. Regression tests added in `tests/test_pregame_timestamps.py` and `tests/test_pregame_scoring.py`. Existing archived history without verified kickoff evidence remains excluded. Confirm current CI passes before sign-off.
- [x] Reconcile README with implemented features and verified workflows. Evidence: commit 051ef3c documents run 41341132284, live refresh provenance, retrospective-versus-prospective accuracy, and remaining limitations. Handoff remains historical context.

## Release criteria

Release Version 1.0 only when all gates above have recorded evidence. Never claim prediction accuracy with zero archived completed games. Do not retire the Google Sheet until parity is verified. A failing deploy or stale live data blocks release.

## Next work batch

1. Confirm current HEAD tests/build/deploy succeed and deployed report bytes match the validated artifact.
2. Verify six sections at mobile widths and archived forecast eligibility; fix only blockers.
3. Tag v1.0.0 after recording evidence for every open gate.
