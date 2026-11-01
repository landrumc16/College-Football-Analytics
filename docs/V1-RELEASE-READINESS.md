# Version 1.0 — Release Readiness

Status: **In progress**. Do not describe the dashboard as 100% ready until the gates below are evidenced.

## Release gates

- [x] Mobile-first navigation consolidated into a section selector, with consistent Title Case.
- [x] Last-data-update timestamp and source visible in the dashboard (committed; deployment pending verification).
- [ ] Validate the latest Pages build and deploy after final changes. Record workflow run URL and commit SHA.
- [ ] Verify the deployed site on narrow mobile viewports (320, 375, 390, 430 px), portrait orientation; no horizontal clipping; dropdowns, filters, rankings, schedule, CFP, and hypothetical matchup all usable.
- [ ] Validate live report invariants: roster/team count, unique schedule IDs, source and retrieval timestamp, valid probabilities, standings and bracket consistency, complete vs pending game separation. Predictions may include non-FBS games not present in the FBS-filtered school schedule.
- [ ] Verify scheduled refresh and publication end-to-end. Confirm the deployed report timestamp advances; failure must not silently masquerade as a fresh report.
- [ ] Reconcile model output against the reference Google Sheet with documented tolerances; retain Sheet until parity is established.
- [ ] Implement and test forecast accuracy using only archived, genuinely pregame predictions. Report sample size and coverage; no retrospective reconstruction. Track winner accuracy and probability calibration / Brier score when sample is sufficient.
- [ ] Check 12-team CFP selection and seeding assumptions against the applicable 2026 rules; label modeling approximations explicitly.
- [ ] Review accessibility, loading/error/empty states, and keyboard/touch controls.
- [ ] Update README with verified implementation, deployment evidence, data limitations, and operator recovery instructions.

## Evidence and known limitations

- GitHub Actions run 41323699979: dashboard build and deploy both succeeded before this readiness pass.
- Earlier run 41319533722 failed on an invalid assertion that all predictions were in the FBS-filtered schedule; fixed in commit deb259a.
- A successful CI build is not a substitute for testing the live Pages site.
- Performance vs. Expectations is intentionally blank until completed games have valid archived pregame forecasts. Do not manufacture historical predictions.
- Frozen 2026 roster/prior inputs are currently supported; future seasons require explicit baseline work.
- Historical parity, live phone interaction, and accuracy validation are not yet signed off.

## Release decision

**NO-GO** until every mandatory gate has evidence. Keep the scope surgical; prioritize correctness and release confidence over new features.
