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

## Updated V5 source workflow evidence — November 9, 2026

- Successful [historical-coverage run 42728326802](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42728326802), **branch `v5-development`**, exact tested SHA `b82fc1a5b5d30cd0f8156573737118d4a674e4dd`. GitHub reports the job and every listed step concluded `success`, including source retrieval, source validation, research calculations, and upload.
- Artifact `v4-historical-source-coverage`, ID `13723239129`, reported ZIP size 1,088,084 bytes, GitHub-reported digest `sha256:96d4e72aed06b67e6705af316232a36ca6529b318ae16010ef0b4bb44e725a47`, uploaded 2026-11-10 UTC. The artifact was downloaded during the V5 review. Unlike the earlier V3 artifact, the updated workflow is configured to include the original season Parquet source bytes for independent inspection.
- The earlier `main` run `42727994671` is **not** evidence that the updated `v5-development` workflow ran. The V5 run above supersedes that branch ambiguity.
- **Publication is still blocked.** A successful source-coverage workflow and its internally consistent source hashes do not establish independently sourced preseason/final AP and Coaches poll observations or a defensible comparable opponent-adjusted strength scale. The existing scale diagnostics prohibit treating retrospective Elo as verified cross-season rankings. No `source_review_attested` publication has been authorized by these checks.
- **Next required deliverable:** source-specific, season-specific poll records for a bounded cohort, independently reviewed comparable strength observations, and a published `v4-program-intelligence.json` with targeted calculation, provenance, and browser tests. Keep the research-only retrospective walkforward separate from genuine archived pre-kickoff predictions.
