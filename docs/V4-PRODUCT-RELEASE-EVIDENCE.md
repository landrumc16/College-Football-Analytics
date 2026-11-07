# Version 4.0 product-only release evidence — November 6, 2026

Release candidate: `adb87d8e8b954afb8df7d0ae3141a2a2e4bd45fb`
Pull request: https://github.com/landrumc16/College-Football-Analytics/pull/12
Approved scope: November 6 amendment in `docs/V4-ROADMAP.md`.

## Verified CI on candidate
- Python model tests: https://github.com/landrumc16/College-Football-Analytics/actions/runs/42332490865 — success.
- V4 development validation (frontend/build/Chromium mobile journeys): https://github.com/landrumc16/College-Football-Analytics/actions/runs/42332490835 — success.
- V3.4.2 validation: https://github.com/landrumc16/College-Football-Analytics/actions/runs/42332585694 — success.
- V3 research validation: https://github.com/landrumc16/College-Football-Analytics/actions/runs/42332585668 — success.
- V2 historical checks: https://github.com/landrumc16/College-Football-Analytics/actions/runs/42332585644 — success.

## Product features
- Team Profiles, Program Rankings, Hype Index, Program Trajectory, momentum, Stock Watch, contenders, prediction explanations and full-season schedules implemented.
- Comparison pages link to Team Profiles; search, favorites, CFP and mobile journeys included in browser validation.
- Coaching/coordinator, roster/transfer and opponent-specific factors explicitly unavailable where not verified.
- Historical rankings/hype remain unpublished unless verified research asset passes the schema/provenance gate. No invented historical metrics.

## Model safeguards
- The release guard checks `model_id=workbook_2026_baseline`, `model_status=incumbent_not_v3_promoted`, and `historical_study=retrospective_research_only`.
- Challenger is research-only; no claim of improved predictive accuracy and no promotion.
- This identity guard is **not** an independently reconstructed bit-for-bit V3.4.2 parity proof.

## Remaining production acceptance
- Verify the complete validation suite on the final release-evidence commit.
- Merge approved product-only release and verify the actual `main` deployment and live GitHub Pages UI.
- Owner acceptance remains outstanding until live review.
