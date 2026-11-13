# V5 authentic forecast-ledger recovery — 2026

**Development branch:** `v5-development`. **Source:** `data/pregame-2026-history.json` (Git blob SHA `6e497d1401ec4ef84809775de1f0f722088bbdb0`), inspected November 13, 2026.

## What the actual retained file contains

- **850** keyed records, with **830** records carrying `source=generated_before_kickoff`, `model_id=workbook_2026_baseline`, `forecast_recorded_at`, `source_retrieved_at`, and `scheduled_kickoff_at`. In the retained file, all 830 satisfy `source_retrieved_at <= forecast_recorded_at < scheduled_kickoff_at` when parsed as timestamps.
- **20** additional records carry `source=previously_published_forecast` and lack model ID, source retrieval time and scheduled kickoff time. These **must not** enter the authenticated V5 evaluation without separate source and kickoff corroboration.
- Counts by recorded week: 9: 20; 10: 316; 11: 315; 12: 130; 13: 68; 15: 1. The 830 candidate entries include future games as of November 13; they are **not** all eligible for accuracy scoring.
- The 830 candidate entries are **timestamp-consistent within the stored file**, but this does not independently establish immutability, original publication time, settled outcomes, or absence of historical alteration.

## Shortest remaining M4 execution path

1. Join the 830 candidate rows to independently sourced **final** game outcomes by canonical game ID; exclude games not yet completed and exclude all 20 legacy records unless independently rehabilitated.
2. Verify source/retrieval timestamps against available historical commits or workflow artifacts and kickoff times against the source schedule. Explicitly document coverage and excluded rows.
3. Feed only verified, settled rows to existing `src/cfb_analytics/v5_forecast_evaluation.py` using its existing schema (`game_id`, `model_id`, `prediction_time`, `kickoff_time`, `home_win_probability`, `home_won`).
4. Publish descriptive accuracy, Brier, log loss and calibration only for the **verified settled subset**, with denominator and source provenance; do not imply ten-year archive coverage, or authorize challenger promotion.
5. Complete V5 acceptance and request owner approval before merging PR #15.

**Release status:** A real candidate pregame archive has been located, substantially narrowing the M4 blocker. **Authentic verified accuracy is not yet established.**
