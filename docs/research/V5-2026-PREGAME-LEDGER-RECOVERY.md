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


## November 13 cutoff — concrete scoring cohort

At `2026-11-13T00:00:00Z`, of the 830 internally timestamp-consistent `generated_before_kickoff` candidates:
- **323** had a scheduled kickoff earlier than the cutoff: **316** recorded as week 10 and **7** as week 11.
- **507** had a scheduled kickoff on or after the cutoff: **308** week 11, **130** week 12, **68** week 13, **1** week 15. Exclude all from the cutoff's scored denominator.
- The **20** `previously_published_forecast` legacy records remain excluded for incomplete pregame provenance.

**Important:** kickoff having passed does not establish a completed game or a correct outcome. The 323 are a *maximum candidate pool*, not a verified scored denominator. Final-score joins, game eligibility and source/commit-history corroboration must reduce or confirm this pool before metrics are released.

**Data access limitation during this pass:** `data/cfbd-2026-games.json` is ~1.06 MB and the available GitHub connector refused its full contents as oversized; a short line-range read also yielded no usable game rows. Therefore no game-score join or accuracy computation was performed in this pass. The shortest recovery is to run the existing repo pipeline/CI against the full file in a checkout or retrieve a suitably sized verified results artifact. Do not substitute fabricated outcomes.
