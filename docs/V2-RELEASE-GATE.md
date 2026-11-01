# V2 release gate — evidence, not estimates

## Current decision: HOLD (2026-11-01)

V2 lives on `v2-development` and draft PR #2. Do **not** merge until all gates below pass.

| Gate | Current evidence | Release requirement |
| --- | --- | --- |
| Python regression | Workflow configured; no confirmed passing check observed | Successful full pytest run on current PR head |
| Spreadsheet parity | Five observed prediction rows in `tests/test_workbook_live_parity.py` | Passing parity test in CI |
| Historical coverage | Benchmark records eligible games, matched games, missing forecasts and unverified timestamps | Audited game-level pregame forecast snapshots; report coverage and exclusions |
| Model comparison | `python -m cfb_analytics.paired_cli` implemented | Run on identical matched FBS games; publish accuracy, Brier and log loss by season |
| Live V1 safety | Changes isolated to V2 branch | Confirm production dashboard still works after merge |

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
