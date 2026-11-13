# Historical poll audit — 2016–2025 (in progress)

**Scope:** 40 AP/Coaches preseason/final top-25 snapshots, 2016–2025. This is an evidence log, **not** a certification that all 40 snapshots have been independently verified.

## Input evidence

- GitHub Actions run [43434822925](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43434822925), artifact ID `14042222413`, source CSVs and SHA-256 manifests.
- 86 ranked ESPN IDs mapped to canonical team names; 1,720 program-season-poll records. This establishes structural completeness, **not historical accuracy**.
- Independent cross-checks: [College Poll Archive preseason leaders](https://www.collegepollarchive.com/football/ap/research/previous-rank-preseason-number-1.cfm), [national champions](https://www.collegepollarchive.com/football/ap/research/national-champion-previous-next.cfm), [AP preseason/final turnover](https://www.collegepollarchive.com/football/ap/research/preseason-final-poll-turnover.cfm), and [2025 AP preseason announcement](https://apnews.com/article/c6a39b07f29a53451b4557008002969d).

## Cross-check findings

| Season | Stored AP preseason #1 | Stored AP final #1 | Stored AP turnover | External turnover | Status |
|---|---|---|---:|---:|---|
| 2016 | Alabama | Clemson | 11 | 11 | Anchor checks agree; full rows pending |
| 2017 | Alabama | Alabama | 9 | 9 | Anchor checks agree; full rows pending |
| 2018 | Alabama | Clemson | 11 | 11 | Final AP tied No. 7 Florida/Georgia retained; full rows pending |
| 2019 | Clemson | LSU | 8 | 8 | Anchor checks agree; full rows pending |
| 2020 | Clemson | Alabama | 10 | 9 | **Mismatch — investigate** |
| 2021 | Alabama | Georgia | 14 | 14 | Anchor checks agree; full rows pending |
| 2022 | Alabama | Georgia | 15 | 15 | Anchor checks agree; full rows pending |
| 2023 | Georgia | Michigan | 8 | 8 | Anchor checks agree; full rows pending |
| 2024 | Georgia | Ohio State | 13 | 13 | Anchor checks agree; full rows pending |
| 2025 | Ohio State (week 2, invalid) | Indiana | 11 | 12 | **Invalid preseason source; must replace** |

## Publication blockers

1. Replace the 2025 week-2 AP and Coaches preseason data with authentic August 2025 poll rankings and separate provenance.
2. Resolve the 2020 AP turnover discrepancy, including special 2020 poll eligibility/context.
3. Independently compare **every ranked team and rank** across all 40 snapshots (1,000 top-25 placements), not merely #1 and turnover anchors; confirm 2018 ties and other tied ranks.
4. Independently cross-check 2016–2025 game outcomes and season aggregation for program trajectories, including 2020 treatment.
5. Only then attest source review and allow Hype Index/Report Cards to publish. Do not promote the research-only artifact or fabricate passing status.

**Result:** Structural audit passed; historical-source audit **not complete**. This log records real discrepancies to resolve, not a release approval.


## 2026-11-13 focused 2020 AP reconciliation

Compared all 25 **2020 AP preseason** placements from the permanent archive with College Poll Archive's independently displayed [2020 preseason poll](https://collegepollarchive.com/football/ap/seasons.cfm?appollid=1169). **All 25 team/rank pairs agree**. The archived [2020 final AP poll](https://collegepollarchive.com/football/ap/seasons.cfm?appollid=1185) also lists the same 25 team/rank pairs (including 2020 postseason newcomers). The ten preseason programs missing from the final top 25 are **LSU, Penn State, Oregon, Auburn, Wisconsin, Michigan, Minnesota, UCF, Utah and Tennessee**. Thus the actual 25-to-25 set comparison is **10**, while College Poll Archive's [summary table](https://collegepollarchive.com/football/ap/research/preseason-final-poll-turnover.cfm?filter=Top25) reports **9**. This is a **discrepancy in the external summary statistic**, not evidence that we should alter any individual ranked team or substitute data. The underlying 2020 top-25 snapshots are retained unchanged; do not overwrite the observed count with 9. The special 2020 season should still be flagged when interpreting program trajectories. This reconciliation is limited to AP 2020 and does not certify the other snapshots, Coaches polls, or season results.
