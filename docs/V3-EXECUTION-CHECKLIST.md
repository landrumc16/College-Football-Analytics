# V3 implementation and release checklist

**Branch:** `v3-development` · **PR:** #3 (draft) · **Production:** V2 unchanged

## Immediate execution: historical data benchmark

1. Identify existing historical game JSON inputs used by `scripts/walkforward_baseline.py`; do not fabricate source data or timestamps.
2. Run the unchanged V2 Elo baseline on the exact historical input population and reconcile the published V2 scorecard.
3. Run `python -m scripts.v3_elo_study <game-json-files...> --holdout 2025 --output artifacts/v3-elo-study.json`.
4. Confirm 2022–2024 development and 2025 holdout game counts and exclusions. Review season-specific performance and calibration. The five-model grid is frozen; **do not tune again using 2025 holdout**.
5. Select the development-best candidate only if holdout evidence and stability justify added risk. Otherwise keep the incumbent. No production model promotion based on retrospective accuracy alone.

## M3–M6 delivery gates

- **Prediction engine:** preserve existing behavior until the selected candidate is verified; add model version and testable fallback.
- **CFP:** test conference title and seed behavior against actual documented rules; display committee approximation caveat.
- **Poll comparisons:** use verified dated AP/Coaches/CFP snapshots only; missing polls must stay missing, never invented.
- **Dashboard:** preserve rankings, predictions, conferences, CFP, schedule, What If; add historical model diagnostics only where data exists.
- **CI:** Python tests, frontend build, mobile smoke, historical data integrity, deployed report parity and production deployment must pass.
- **Closeout:** document actual model comparison, exact data population, final commit, CI runs and Pages URL. Merge only when gates pass.

## Execution constraints

No speculative model expansion; keep the original workbook reference, FCS rating influence, and strict separation of reconstructed historical backtests from archived pregame predictions. A passing unit test does not establish real-data accuracy or release readiness.

## Known verification gap

This document does not assert historical runs or GitHub Actions passed. The current V3 research scripts and CLI are committed, but full historical-data execution, candidate evaluation and production validation remain outstanding.
