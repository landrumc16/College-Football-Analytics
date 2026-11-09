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

## November 8 — passing executable candidate (after browser regression fix)
- Exact executable commit: `19e5db95124a30aae8a265bf80ccbabd55d3f5ab`.
- [V4 development validation 42544623801](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544623801): **success**. Job `validate` passed Python regressions, challenger release guard, frozen workbook parity, reproducible 2026 baseline, source/fixture provenance, baseline coverage, frontend production build, validated incumbent report staging, Chromium mobile/PWA/historical journeys, and production PWA artifact verification.
- [Python model tests 42544623798](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544623798): **success**, including `pytest` and dashboard build jobs.
- V4 validation artifacts: `v4-mobile-browser-evidence` (artifact 13643145387; 30,852,825 bytes) and `v4-frozen-2026-retrospective-baseline` (artifact 13642753007). Artifact existence **does not establish human visual acceptance**.
- **Remaining owner-approval gates:** visually inspect actual desktop/mobile screenshots, verify each release-required feature and independently reviewed historical publication coverage, record release notes and any non-blocking limitations. Historical research absent independent review must stay unavailable; no promotion of challenger.
- `main` and production deployment remain untouched.

## November 8 — post-visual-fix candidate validation and screenshot review
- Latest executable commit: `8833eef8fbfe0aae8b2e59595fa0b64e2ecd1ef2`. The visual change corrects Team Profile tile contrast by replacing an unintended light fallback background with a dark collegiate surface and readable foreground/label colors.
- [V4 development validation run 42544993535](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544993535): **success**. [Python model tests run 42544993538](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42544993538): **success**. Both target the exact executable SHA above.
- Downloaded actual `v4-mobile-browser-evidence` artifact 13642692757 from run 42544993535 (30,949,629 bytes), containing 40 screenshots across home, rankings, historical hype, trajectory, program rankings, Team Profile, stock, contenders, CFP, and predictions at widths 375, 390, 768, and 1536. Inspected the contact sheet and the top 1200 pixels of `profile-390.png` directly; the previously observed white-on-light Team Profile metric defect is resolved in this screenshot. This is a **targeted** visual acceptance, not an assertion that every full-length image has been reviewed at native scale.
- Source limitations remain visible: the captured Team Profile shows unavailable historical metrics and unavailable poll data where the validated report does not supply them; no historical ranking, hype, or trajectory value is invented.
- **Remaining release gates:** full-resolution inspection of remaining long-page screenshots, source-coverage/product acceptance against the November 8 amendment, and explicit owner authorization. The current screenshots are from the test fixture, not proof of public production deployment. No merge or deployment.

## November 8 — current candidate validation and latest screenshot package
- **Latest executable candidate:** `cad394fe52a2566f60582b66eec1aca4e02dc1ae` (AP/Coaches current-season selector, conference discovery, and browser regression handling verified absent poll fixtures).
- [V4 development validation run 42557010119](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42557010119): **success**. [Python model tests run 42557010236](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42557010236): **success**. Both tested the candidate SHA.
- Retrieved `v4-mobile-browser-evidence` artifact **13647902100** from successful run 42557010119, size **30,958,235 bytes**; confirmed **40 PNG captures** for home, rankings, hype, trajectory, programs, Team Profile, stock, contenders, CFP, and predictions at widths 375, 390, 768, and 1536. Inspected a composite of the 390px and 1536px captures. The visible dark theme is consistent; no obvious blank-route failure in the contact sheet. This overview is **not** full-resolution visual signoff, especially for long scrolling pages.
- Historical publication remains conditional on independent source-review attestation; missing historical data must not be represented as completed 10-season analysis. Current-season poll comparisons are separately gated by actual dated poll availability. No experimental challenger promotion.
- **Release decision:** HOLD. Before requesting owner approval, finish full-resolution visual acceptance and a source-backed acceptance disposition for every remaining release-required historical/research feature. No merge or deployment authorized.

## November 8 — historical-asset error handling verified
- **Executable candidate:** `76a62a805d0fade40e4d0a123440b3199042ea1f` changes the historical discovery fetch to reject non-JSON responses before parsing. This prevents a missing optional historical asset from leaking an HTML/JSON parse exception into the fan-facing unavailable state.
- [V4 development validation 42562972604](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42562972604): **success**; [Python model tests 42562972693](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42562972693): **success**. Both tested the exact executable candidate.
- Historical source authenticity, complete ten-season publication coverage, and full-resolution visual acceptance remain open. Automated success does not satisfy those gates. **No production merge or deployment authorized.**

## November 9 — final-candidate visual evidence and disposition

- Latest tested executable SHA: `0096dab52584541c4b5234a0a2102681848c22b4`. V4 validation [42563594154](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42563594154) **success**; Python model tests [42563594199](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42563594199) **success**.
- Retrieved the exact-run browser artifact `v4-mobile-browser-evidence` (artifact **13650163957**, 30,964,516 bytes), containing 40 PNGs: home, rankings, historical hype, trajectory, historical program rankings, Team Profile, stock, contenders, CFP and predictions at **375, 390, 768, 1536** pixels.
- Opened the 390px full-page Hype Index screenshot and visually reviewed a top/middle/bottom contact sheet for all ten 390px views. The pages render with consistent dark styling; no blank screen was apparent in this sample. Long tables and tall mobile pages remain a usability concern, especially current poll comparisons and data-heavy stock/CFP views. This review is **not** full-resolution acceptance of every screenshot at all four widths.
- The newly added first-25 historical table control is part of the tested candidate, but the captured Hype Index page still contains a long **current-season poll comparison** table; the first-25 historical limit does not shorten that independent table.
- **Historical provenance disposition: not independently verified.** The existing format/provenance guards and automated tests do not authenticate all real AP/Coaches poll and schedule-adjusted ten-season sources. Under the November 6 decision, unsupported historical Hype Index, Program Trajectory and Program Rankings metrics must remain explicitly unavailable. This is an accepted *publication safeguard*, not evidence that the requested ten-season research has been completed.
- **Release decision: HOLD for owner approval request.** Before presenting as fully ready, finish full-resolution desktop/mobile visual acceptance and decide whether the honest unavailable historical pages meet the approved release-required feature threshold. No production merge, deploy, or challenger promotion.
