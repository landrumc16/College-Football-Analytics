# V2 release gate — evidence, not estimates

## Current decision: V2 research beta CI verified; production release pending (2026-11-02)

V2 lives on `v2-development` and draft PR #2. Do **not** merge until all gates below pass.

| Gate | Current evidence | Release requirement |
| --- | --- | --- |
| Python regression | Passed: Python model tests run 41369068578 and historical evaluation run 41369068584; historical-data run 41369147125 | Successful full pytest run on current PR head |
| Spreadsheet parity | Five observed prediction rows in `tests/test_workbook_live_parity.py` | Passing parity test in CI |
| Historical coverage | Real 2022–2025 schedule audit passed: 3,174 completed FBS-FBS games; 485 FBS-other completed games; zero missing FBS kickoff; artifact 13108965581. No verified archived pregame model forecasts | Audited game-level pregame forecast snapshots; report coverage and exclusions |
| Model comparison | Retrospective Elo walk-forward completed: 3,174 FBS games; accuracy 66.51%, Brier 0.21363, log loss 0.61582. This is NOT workbook-model parity or paired model comparison | Run on identical matched FBS games; publish accuracy, Brier and log loss by season |
| Live V1 safety | Changes isolated to V2 branch; dashboard smoke verification still required | Confirm production dashboard still works after merge |

## Run the benchmark

```bash
python -m pytest -q
python -m cfb_analytics.paired_cli --games games.json --workbook workbook.json --candidate candidate.json --output benchmark.json
```

Each JSON input must be an array of records matching `HistoricalGame` or `ArchivedForecast`. Forecasts require **actual pregame** `generated_at` and `input_retrieved_at` timestamps; do not manufacture timestamps from kickoff dates. The workbook forecast must use independent model probability (Predictions column N), **not** market-assisted displayed probability (column H). FCS game results remain relevant to rating development, but FBS-vs-FCS games are excluded from this FBS-vs-FBS accuracy denominator.

The workbook's previously reported ~71.7% model and ~73.2% market accuracy are **unverified claims**, not V2 results. A retrospective reconstruction must be labeled as such and cannot be passed off as an archived pregame forecast.

## Release decision

Do not merge or claim improvement over betting lines unless the verified sample and metrics support it. A small or unavailable archived sample warrants a clearly labeled **research beta** rather than a validated accuracy release.

## Source audit

The connected spreadsheet contains aggregate 2022-2025 backtest claims, but its live Games and RatingHistory tabs cover 2026. No separate game-level historical forecast archive was found in the connected Drive search. The claimed 2,998-game comparison therefore remains unverified. A chronological reconstruction using historical games and season-specific divisions is required. Reconstructed forecasts must be labeled retrospective, never archived pregame.

## Verified historical baseline evidence (run 41369147125)

Source: SportsDataverse season schedules, 2022–2025; GitHub Actions artifact `v2-historical-data-2022-2025` (ID 13108965581). The job completed successfully, including baseline regression tests and artifact upload. This is a **retrospective Elo baseline**, not the workbook model, and does not certify pregame archived predictions.

| Season | FBS-FBS games | Accuracy | Brier | Log loss |
| --- | ---: | ---: | ---: | ---: |
| 2022 | 776 | 64.30% | 0.22900 | 0.65028 |
| 2023 | 792 | 68.18% | 0.20748 | 0.60399 |
| 2024 | 798 | 64.91% | 0.21566 | 0.61925 |
| 2025 | 808 | 68.56% | 0.20288 | 0.59092 |
| **Overall** | **3,174** | **66.51%** | **0.21363** | **0.61582** |

**Outstanding release gates:** independently run the workbook-derived model over the same historical game population (or explicitly narrow release claims to a baseline research beta); verify dashboard smoke and full PR head CI; then approve PR #2. Do not use the unverified 2,998-game spreadsheet summary as a comparable scorecard. Do not merge the draft PR merely because the Elo baseline passes.

## November 1 follow-up: chronology correction

Commits `1e446d94` and `1e8f3b4b` delay outcome updates until four hours after kickoff and add a same-day leakage regression. Python model CI run `41369860070` and historical evaluation CI run `41369860111` both passed. The earlier metrics were temporarily superseded; the corrected full audit subsequently reproduced the same aggregate values (see verified run below). No claim of original workbook historical performance is authorized by the baseline run.

## Corrected historical workflow: verified (2026-11-02)

[Run 41370501226](https://github.com/landrumc16/College-Football-Analytics/actions/runs/41370501226) on `v2-development` commit `ff92bc41` completed successfully, including importer, regression tests, four-season baseline, and new integrity assertions. Artifact `v2-historical-data-2022-2025` ID `13108104121` uploaded successfully.

**Corrected retrospective Elo baseline:** 3,174 completed FBS-FBS games, winner accuracy **66.5091%**, Brier **0.213628756**, log loss **0.615816389**. The corrected same-day outcome-availability guard did **not change the aggregate results** in this dataset. FBS-FCS games inform ratings but are excluded from accuracy. This is not a verified workbook-model backtest, archived pregame forecast, or market comparison. Historical data integrity gate is **PASS**; remaining release decision concerns scope and dashboard integration/smoke verification.

## Final scope reconciliation

PR #2 changes historical research tooling, tests, and documentation only (23 changed files); it does not implement or verify a distinct V2 frontend. The existing V1 React/Vite dashboard remains the production application. **Do not present a merge of PR #2 as completion of the full V2 dashboard.** A research-engine-only merge may be approved separately after current-head CI and compatibility review, with explicit release labeling. The spreadsheet's 71.7% and market 73.2% claims remain unverified and must not appear as reproduced accuracy. Full V2 UI release requires a demonstrable frontend feature boundary and smoke checks.

## Final preview CI evidence (2026-11-02)

- [V2 historical evaluation workflow run 41371557374](https://github.com/landrumc16/College-Football-Analytics/actions/runs/41371557374): **PASS**, including full Python suite, frontend TypeScript/Vite production build, and published research-summary payload smoke assertions.
- [Python model workflow run 41371557433](https://github.com/landrumc16/College-Football-Analytics/actions/runs/41371557433): **PASS**.
- Verified head: `5fa4e63174a6f01f3d45fa233dba9eba65e02a59`. PR #2 remains draft and mergeable at this checkpoint. The CI check is a **build/data smoke**, not an interactive browser playtest or deployed-site smoke.
- The intended release scope is **V2 research beta**: existing dashboard plus clearly labeled 2022–2025 retrospective Elo scorecard, with no workbook-model or market-outperformance claim. Production Pages deployment has not been verified on this branch. Keep V1 live until explicit merge approval and post-merge Pages smoke.
