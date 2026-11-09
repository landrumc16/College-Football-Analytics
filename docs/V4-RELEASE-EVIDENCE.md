# Version 4.0 — Release verification evidence (in progress)

## Candidate and authorization
- Development branch: `v4-development`.
- Candidate baseline before this ledger: `dbad939e435842973e9bc70716d09b9b62dacee5`.
- Production branch: `main`; **no merge or release authorization granted**.
- Release model: existing V3.4.2 incumbent; experimental challenger remains research-only under the November 6 amendment.

## Observed CI evidence (2026-11-08)
- Workflow run: https://github.com/landrumc16/College-Football-Analytics/actions/runs/42516668196
- Job `validate` (128841074440): completed **success**.
- Successful steps: Python regression suite; challenger-promotion guard; frozen workbook parity; reproducible retrospective baseline; provenance and coverage checks; dashboard build; Chromium mobile/PWA/historical journeys; production PWA artifact verification.
- Uploaded artifacts: `v4-frozen-2026-retrospective-baseline` (13630978948) and `v4-mobile-browser-evidence` (13630934085, 12 screenshots).
- **Critical scope limitation:** Artifact metadata identifies the workflow head as `main` at `c8a92ba7fa7d083c6acdfc950b89f091094151f4`, NOT `v4-development`. Thus this successful run does not certify the V4 development candidate. Do not claim otherwise.
- Retrospective baseline is not a genuine pregame prediction archive.

## Candidate-specific passing validation — 2026-11-08
- Workflow: https://github.com/landrumc16/College-Football-Analytics/actions/runs/42516899396
- Tested branch: `v4-development`; tested SHA: `dc870f3cf94691627580bd132d76f13a1ba99564` (verified from uploaded artifact workflow metadata).
- Job `validate` (128841788757): **completed / success**, all steps successful.
- Verified passing checks: Python regression suite; challenger guard; frozen workbook parity; retrospective baseline generation; baseline source and coverage checks; frontend production build; incumbent season report staging; Chromium mobile/PWA/historical journeys; production PWA artifacts.
- Artifacts: retrospective baseline `13632175551`; browser evidence `13632135845` (uploaded, not yet visually inspected).
- This is the verified tested code candidate; any subsequent documentation-only commit must be distinguished from the tested SHA. No merge or production deployment is implied.

## Product and research release boundaries
- Consolidated Team Profiles, historical discovery views, Stock Watch, and Contenders/Pretenders have been implemented with explicit unavailable states for unsupported data.
- Historical publication requires reviewed source attestation and descriptive-only status; no unsupported historical ranks or movement may be synthesized.
- Stock Watch four-week movement requires real timestamped weekly snapshots; otherwise unavailable.
- Contender classifications require independent validated evidence; otherwise unavailable.
- Challenger and unverified coaching/roster factors must not be attributed to production predictions.
- Historical data coverage and actual user-facing completeness remain subject to candidate-specific verification.

## Outstanding release gates
1. **Satisfied for code candidate `dc870f3`:** V4 validation ran on `v4-development`, completed successfully, and produced artifacts. Revalidate if executable code changes.
2. Inspect actual candidate desktop/mobile screenshots and confirm Team Profile, historical pages, navigation, favorites, predictions, CFP, and missing-data behavior.
3. Confirm all M6 acceptance requirements against the November 6 scope amendment; record any verified limitations.
4. Freeze the tested candidate SHA, finalize release notes, and obtain explicit owner approval **before** merging.
5. After approval, verify production deployment, live commit, desktop/mobile behavior, and final acceptance.

This ledger records observed evidence, not a release declaration.

## Post-validation product changes (not yet CI-certified)
- After validated executable SHA `dc870f3`, the V4 development branch received Hype Index and Program Trajectory discovery differentiation (`2812148`), responsive browser assertions (`83ff354`), standalone compact Poll Comparison navigation and display (`9c134a0`), and browser coverage (`221e56c`).
- The owner-approved Poll Comparison requirement is now recorded in `docs/V4-ROADMAP.md` (November 8 amendment). It is limited to School / Our Model / AP / Coaches / CFP, approximately 30 rows, with verified-source fallbacks.
- **Verification status:** no passing CI run for these executable commits has been observed in this work session. Existing run `42516899396` does not certify them. Re-run V4 validation and inspect actual screenshots before requesting owner approval.
- **Known follow-up:** current poll table uses a deterministic union/truncation by minimum observed rank, but needs an explicit fixture test confirming useful overlap and the 30-row cap when the union exceeds 30. Do not claim the overlap acceptance criterion is verified.
- No merge to `main`, challenger promotion, or production deployment authorized.

## November 8 follow-up — trajectory windows and source-backed chart
- Development branch implementation commits: `e0c25cc` source-backed strength series; `2054cfd` interactive historical chart with gaps; `43143bb` and `96290b3` regression/browser assertions; `dac5e72` five-year trajectory calculation; `e3df3a2` shared payload integration; `be986a8` national trajectory table; `ce27c8d` Team Profile; `a203c78` five-year regression assertions.
- **Verification not yet established:** No full Python, frontend, Chromium, or PWA run was executed for these changes in this session. The previous successful CI run `42516899396` covers only `dc870f3`.
- **Release gates remain open:** current candidate build/test, reviewed source publication and coverage, actual desktop/mobile screenshot review, product acceptance and release notes. A committed test is not a passing test.
- **Production unchanged:** no merge, deployment, or challenger-model promotion.

## November 8 — verified workflow status for conference-filter candidate
- Commit `d1fa7ee5f60a7b057f3e76ee90c0add31743d97e` passed GitHub Actions run [42544406627](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544406627): `pytest` and `dashboard-build` jobs both succeeded. Dashboard job generated historical demo JSON, validated it, built the dashboard, validated the published report and uploaded a preview artifact.
- Separate V4 development validation run [42544406648](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544406648) was still **in progress** when inspected; do not infer browser, PWA, historical parity or provenance success from the passing build/test workflow alone.
- Release remains gated on completed V4 validation, source-review evidence, visual inspection of actual screenshots, and explicit owner approval.
