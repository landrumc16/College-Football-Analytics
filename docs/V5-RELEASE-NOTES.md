# Version 5.0 release candidate

V5 adds independently corroborated historical program intelligence and genuinely
archived prediction-performance reporting to the existing public application.
The incumbent V4 prediction engine, rankings, schedules, CFP forecasts, This
Week homepage, school search, favorites and PWA remain the product foundation.

- Hype compares authentic AP/Coaches preseason expectations with final Top 25
  outcomes across 2016–2025, keeping both polls separately traceable.
- Trajectory distinguishes 3/5/10-year win-rate levels from annual direction,
  explicitly excluding the disrupted 2020 season.
- Report Cards use one shared national peer contract, numeric category scores,
  the approved letter bands and an equal one-third overall score. Unsupported
  coverage remains N/A. Complete historical grades cover 127 of 138 current
  FBS programs; current Strength covers all 138.
- Team Profiles, Programs, Hype, Trajectory and Compare share these results.
- Prediction evidence verifies 65 original Weeks 10–11 forecasts before kickoff and
  independently matches all final scores. Research & Data shows coverage,
  calibration, confidence segments, and an identical-game neutral reference.
- The reusable archive retains source inputs/checksums, independent comparisons,
  accepted records and scoped exceptions, with deterministic offline replay.

Limitations are part of the publication: newer FBS programs lack full historical
windows; disputed exact scores are excluded; unreviewed optional recruiting or
coaching histories are not presented as verified; two partial weeks of forecast evidence
is not a full-season performance claim. Strength and live report timestamps are
shown separately from the historical verification date.

Acceptance uses Python regression and source replay, strict workbook parity,
TypeScript/production build, real Chromium navigation at 375/390/768/1536 pixels,
shared-grade parity, isolated persistent favorites, failure/retry, Android Chrome
emulation and PWA installability/update/offline/recovery checks. Exact tested
revision, workflow results and inspected screenshot artifacts are recorded in
[PR #15](https://github.com/landrumc16/College-Football-Analytics/pull/15).

Production merge requires Andy's explicit approval. V5 is not formally released
until the approved merge, deployment and production smoke verification occur.
