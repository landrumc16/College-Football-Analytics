# Accepted V5 historical and pregame evidence

Verified on November 13, 2026. Original research snapshots are retained unchanged.
This directory contains the independently corroborated publication inputs and
explicit exceptions, not a claim that every archived field is verified.

## Sources and independence

- Historical polls: retained SportsDataverse/ESPN-origin snapshots versus the
  independent College Poll Archive's AP and Coaches columns. All 40 preseason/
  final snapshots (1,000 ranked placements) were compared, including ties and
  complete membership. The missing 2023 final Coaches column was replaced by
  the AFCA publisher's January 10, 2024 final table.
- Three incorrect/missing independent Coaches cells were resolved using first-
  party releases: Mississippi State, 2018 final #25; Virginia Tech, 2020
  preseason #24; Boise State, 2025 preseason #25. Their exact URLs, source
  checksums, accepted facts and replaced cells are in `independent-polls.json`.
  The original primary snapshots did not need these corrections. The separately
  sourced authentic August 2025 preseason snapshots remain authoritative;
  regular-season week 2 was not used as preseason.
- Results: ESPN-origin historical Parquet releases versus NCAA-origin schedule
  CSV releases. Although SportsDataverse distributes both, these are distinct
  upstream feeds, not two ESPN mirrors. The producer documents the independent
  pipeline at https://github.com/sportsdataverse/ncaa-mfb-football-data :
  stats.ncaa.org -> NCAA raw -> NCAA processed -> distribution. Optional ESPN
  event-ID crosswalks are not used as score corroboration.
- Original NCAA schedule/classification bytes are retained with SHA-256 and
  source URLs. Compact canonical ESPN games preserve schedules, opponents,
  dates, divisions and final scores; `espn-coverage.json` records original
  Parquet checksums. Website numerical facts are retained with retrieval URLs
  and hashes rather than copying entire articles.

## Accepted scope and exceptions

- 1,308 of 1,310 team-seasons have identical FBS win/loss totals. The 2020
  Florida State and Georgia Tech discrepancies are excluded. All trajectory
  windows explicitly exclude the disrupted 2020 season, retaining real games-
  played denominators in every other season.
- 7,557 of 7,560 FBS-versus-FBS exact game scores corroborate. Three one-point
  differences remain excluded from the verified exact-score cohort:
  `401014983`, `401021686`, `401309645`. Their winners agree and independently
  corroborated season win/loss totals do not depend on the disputed point.
  `comparison.json` retains both versions. No value was invented or silently
  changed. FBS-versus-FCS source rows are archived but not independently
  certified by this pass and are not used by the historical grading contract.
- The independent 2026 NCAA roster and incumbent roster agree on 138 FBS
  programs. Full historical FBS eligibility and coverage support Hype and
  Trajectory for 127; current Strength for all 138; overall grades for 127.
  Newer FBS programs remain N/A for unsupported historical windows. Idaho is
  retained historically but excluded from the current FBS peer universe.
- AP and Coaches remain separately traceable. The 2020 turnover summary's
  9-versus-observed-10 discrepancy is nonblocking: both underlying 25-team AP
  snapshots corroborate. The 2018 AP Florida/Georgia tie at #7 is preserved.

## Grading contract

Hype is the mean AP/Coaches preseason-to-final movement over 2016–2025.
Unranked uses a capped boundary of 26 only in the index, never an asserted
rank; unranked-to-unranked contributes zero. Retention, dropouts, entrants,
and ranked-to-ranked movement are published separately.

Trajectory uses the mean annual least-squares FBS win-percentage slope over
3/5/10-year windows. Actual calendar years are used, with 2020 excluded.
Winning-percentage levels are context, not direction. A stable elite team
therefore does not automatically receive a rising-trajectory score. Absolute
mean slope within one percentage point/year is labeled stable.

Strength reuses the incumbent V4 current-season rating without a challenger
or model change. The strength as-of timestamp is the actual season report's
retrieval/generation date; historical verification does not make it newer.

Each category uses midrank percentile among sufficiently covered eligible peers
(minimum 80% of the independently declared national universe). Ties share a
percentile; original precision is retained. The overall score is the unrounded
mean of three category scores, with the roadmap's letter bands applied only
for display. Missing categories are N/A and never reweighted.

## Authentic prediction evidence

`published-pregame-2026-11-05.json.gz` contains the original ledger from commit
`42aa772a4d8f3d0095865e2a0946ae7e4813a790`. GitHub Actions run
https://github.com/landrumc16/College-Football-Analytics/actions/runs/42076089302
records that SHA at server time `2026-11-05T17:35:19Z`, before the scored games.
All 65 scored Weeks 10–11 FBS forecasts remain identical to the current ledger.
Their final scores independently match NCAA by team identity and scheduled
calendar date. Five optional ESPN-ID crosswalks differ or are missing, so the
match requires a unique NCAA contest, matching teams/date, and identical scores.
No historical forecasts were regenerated.

The existing evaluator reproduces 42/65 correct (64.6%), Brier 0.2113917032,
and log loss 0.6108603105, with calibration, confidence segments and an identical-
game neutral 50/50 reference. This is two partial weeks' supported evidence, not full-
season accuracy. Coverage and the outcome snapshot timestamp are published.

## Offline replay

```bash
PYTHONPATH=src python -m scripts.reconcile_v5_historical_sources
PYTHONPATH=src python -m scripts.verify_v5_pregame_archive
python -m pytest -q tests/test_v5_verified_publication.py
```

No network or expiring Actions artifact is required. `manifest.json` hashes
retained inputs; NCAA inventory hashes original source bytes. Future source
revisions require a documented reason and renewed comparison. Recruiting,
coaching and other optional unsupported histories remain unavailable.

The live refresh receipt records the successful development-only provider/report
check. Report Card Strength is regenerated by the existing refresh workflow from
retained historical inputs and new incumbent ratings; historical data is not
redownloaded. Independently evaluated forecast outcomes remain a frozen cohort.
