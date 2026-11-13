# V5 historical publication evidence — November 13, 2026

The approved proportional two-source review is complete for the published
historical cohort. Earlier research-only artifacts remain unchanged; they are
superseded for publication by `research/archive/verified/` and its reproducible
accepted inputs. No cross-season Elo scale or challenger promotion is required
or claimed under the approved Program Report Card amendment.

| Evidence | Verified result |
| --- | --- |
| AP/Coaches preseason/final, 2016–2025 | 40 snapshots, 1,000 ranked placements corroborated |
| Team-season FBS win/loss records | 1,308 accepted of 1,310 compared |
| Exact FBS–FBS final scores | 7,557 accepted of 7,560 compared |
| Current national FBS roster | 138 programs; NCAA and incumbent roster agree |
| Hype historical coverage | 127/138 eligible programs |
| Trajectory historical coverage | 127/138 eligible programs |
| Incumbent current Strength coverage | 138/138 eligible programs |
| Complete equal-weight Report Cards | 127 programs; other overall grades N/A |

Sources, raw NCAA files, canonical ESPN games, independent numerical poll
records, source URLs/checksums, identity mapping version, accepted snapshots
and exceptions are retained in the verified archive. The detailed contract,
independent upstream explanation and source-specific resolutions are in
[`research/archive/verified/README.md`](../research/archive/verified/README.md).

Material exceptions are bounded and excluded: 2020 Florida State/Georgia Tech
season-record differences, and three one-point exact-score disagreements whose
winners and season win/loss totals agree. All trajectory windows exclude the
2020 disruption. FBS-versus-FCS raw results are retained but are not represented
as independently certified by this pass or used in historical grading.

The independent poll archive's 2018 Mississippi State final Coaches cell,
2020 Virginia Tech preseason Coaches cell, missing 2025 Boise State preseason
Coaches cell, and absent 2023 final Coaches table were resolved using first-
party university/AFCA releases. The genuine 2018 AP #7 tie and separately
sourced August 2025 preseason polls are preserved. No regular-season poll is
substituted for preseason; no missing rank or score is invented.

Publication artifacts:

- `web/public/v5-program-report-cards.json`: shared grades, coverage, separate
  AP/Coaches retention/dropout/entry facts, and 3/5/10-year direction/windows.
- `web/public/v5-historical-results.json`: corroborated window win/loss totals.
- Programs, Hype, Trajectory, Team Profile and Compare use the same publication.
- The Trajectory calculation now measures annual direction, rather than
  conflating a high win-rate level with improvement; stable elite and weaker
  rising programs are covered by an explicit behavior test.

Offline reproduction (no repeated downloads or expiring artifact):

```bash
PYTHONPATH=src python -m scripts.reconcile_v5_historical_sources
python -m pytest -q tests/test_v5_verified_publication.py
```

The regression test reproduces committed outputs exactly, checks input hashes,
and rejects a modified independent poll. Source review permits these historical
publications; final browser/PWA acceptance is recorded separately on PR #15.
Production `main` and the incumbent prediction engine remain unchanged.
