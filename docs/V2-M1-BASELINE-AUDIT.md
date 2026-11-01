# V2 Milestone 1 — Baseline code audit (2026-11-01)

This is a source inspection, not a completed multi-season validation or a claim of improved accuracy.

## Existing reusable components
- `src/cfb_analytics/ingestion.py`: normalizes CFBD IDs, season, week, opponents, kickoff timestamp, neutral site, and completed scores; rejects conflicting duplicate game IDs.
- `src/cfb_analytics/report.py`: enforces aware UTC timestamps and requires both source retrieval and forecast generation to precede kickoff; restricts reported FBS accuracy to the 138-team baseline.
- `src/cfb_analytics/backtest.py`: deterministic week-by-week replay with preseason baseline, accuracy, Brier and log loss; within-week games are all predicted from the same pre-week ratings.

## Gaps requiring work before V2 model tuning
1. Backtest `evaluation_scope` is explicitly frozen 2026, not multi-season. Multi-season data and year-specific rosters/priors are absent from this evaluation path.
2. Weekly replay is only *week*-granular, not exact chronological kickoff-granular; same-week prior games cannot contribute, even when already finished. This is conservative for leakage but not an exact as-of-game replay.
3. `backtest_weeks` currently scores games with at least one modeled FBS team, including FBS–FCS matchups. Distinguish this from FBS–FBS accuracy and publish counts for both.
4. The fixed `fcs_opponent_rating` is used for unmodeled opponents; test how FCS results affect FBS strength, and report their treatment separately.
5. `ingestion.py` does not retain source retrieval timestamp, division classification, raw provider status, or data version on each game. A versioned historical dataset contract is needed.
6. `report.py` remains explicitly limited to 2026 and 138 frozen teams. Avoid relaxing this until season-specific priors exist.
7. Add calibration diagnostics, reliability bins, season-by-season sample counts and confidence intervals; existing backtest reports accuracy, Brier and log loss only.

## First implementation boundary
- Introduce a standalone, versioned historical-game schema and validators without modifying V1's published report contract.
- Add evaluation eligibility flags: FBS–FBS scored, FBS–FCS contextual, unknown classification excluded pending resolution.
- Build a multi-season, time-aware evaluator with deterministic output and tests; benchmark it against the frozen V1 backtest on overlapping fixtures.
- No dashboard redesign or new prediction model in this milestone.

## Release dependency
The V1 release is visually and technically accepted but `v1.0.0` tag/release has not been verified. Keep model behavior unchanged until that baseline is preserved.
