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

## Product and research release boundaries
- Consolidated Team Profiles, historical discovery views, Stock Watch, and Contenders/Pretenders have been implemented with explicit unavailable states for unsupported data.
- Historical publication requires reviewed source attestation and descriptive-only status; no unsupported historical ranks or movement may be synthesized.
- Stock Watch four-week movement requires real timestamped weekly snapshots; otherwise unavailable.
- Contender classifications require independent validated evidence; otherwise unavailable.
- Challenger and unverified coaching/roster factors must not be attributed to production predictions.
- Historical data coverage and actual user-facing completeness remain subject to candidate-specific verification.

## Outstanding release gates
1. Run `.github/workflows/v4-validation.yml` explicitly on **`v4-development`**, and verify the run's `head_branch` and `head_sha` equal the frozen candidate. Capture full job results and artifacts.
2. Inspect actual candidate desktop/mobile screenshots and confirm Team Profile, historical pages, navigation, favorites, predictions, CFP, and missing-data behavior.
3. Confirm all M6 acceptance requirements against the November 6 scope amendment; record any verified limitations.
4. Freeze the tested candidate SHA, finalize release notes, and obtain explicit owner approval **before** merging.
5. After approval, verify production deployment, live commit, desktop/mobile behavior, and final acceptance.

This ledger records observed evidence, not a release declaration.
