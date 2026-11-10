# V5 Historical Coverage — Retrieved Research Artifact (not publication approval)

**Source evidence:** GitHub Actions run [42701897487](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42701897487), artifact ID `13710699714` (`v3-historical-research`), generated 2026-11-09, originating from `program-intelligence-redesign` SHA `1d4f2e8d861ab7d8321ab360ff966abda338aa3c`.

**Artifact integrity metadata:** GitHub reported ZIP digest `sha256:873ac1f2b2288917524da9b81acdd18e967483a86689f02cc43228055ea0476f`. The ZIP was downloaded and its `coverage.json`, `walkforward_report.json`, `v3-elo-study.json`, and `v3-research-decision.json` were parsed. The source Parquet files and extracted game rows are **not** in this artifact; recorded source SHA-256 values have **not** been independently recomputed from source bytes.

## Historical results coverage

| Season | Extracted FBS-participant games | Completed FBS vs FBS games |
|---|---:|---:|
| 2016 | 873 | 760 |
| 2017 | 874 | 776 |
| 2018 | 884 | 772 |
| 2019 | 888 | 774 |
| 2020 | 570 | 534 |
| 2021 | 887 | 770 |
| 2022 | 896 | 776 |
| 2023 | 910 | 792 |
| 2024 | 919 | 798 |
| 2025 | 934 | 808 |
| **Total** | **8,635** | **7,560** |

The manifest identifies historical schedules at `https://github.com/sportsdataverse/sportsdataverse-data/releases/download/cfb_schedules/cfb_schedules_{season}.parquet` and records per-season source/extract SHA-256, counts, and completeness. These are **reported manifest values**, not independently revalidated source content.

## Research boundaries

- The archived `walkforward_report.json` is explicitly a **retrospective walk-forward baseline**, not frozen pre-kickoff incumbent predictions. Its historical scores must **not** satisfy V5's authentic archived forecast performance gate.
- The Elo study and decision file explicitly do **not** authorize challenger promotion. Production model remains unchanged.
- No independently verified AP and Coaches preseason/final poll observations are included in this artifact. It cannot establish a historical Hype Index.
- No independently validated cross-season comparable strength scale or source-attested historical publication payload is included. The artifact cannot establish published 3/5/10-year trajectories.
- 2020 coverage differs materially from adjacent seasons; no assumption of normal-season comparability is warranted.

## Minimum remaining evidence for completion pass 1

1. Retrieve the **ten-season historical source workflow artifact** containing actual extracted games, team-season records, season strength, schedule context and scale diagnostics; recompute checksums against available source bytes and review cross-season comparability.
2. Locate genuine independently sourced AP and Coaches **preseason and final** rankings with source citations and season-specific team identities for a bounded meaningful cohort.
3. Verify historical calculations and source review; generate the existing `v4-program-intelligence.json` publication contract only for supported coverage. Never set `source_review_attested` without independent review.
4. Execute targeted integrity tests and inspect real Programs, Hype, Trajectory and Team Profile displays. Until then, **Pass 1 remains blocked**, not complete.

This document records retrieved evidence and outstanding source requirements, not a release claim.
