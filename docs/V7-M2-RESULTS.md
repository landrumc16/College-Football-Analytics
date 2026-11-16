# V7 Milestone 2 — Historical Market Archive: results

**Branch:** `v7-development`. **Baseline:** `main` `ec98f28`, plus the approved V7
planning documents (`79ebed1`).
**Verified run:** [43879232428](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43879232428)
at `35d9d75`. Derived outputs were committed by that run as `07d49e9`.

**Determination: BLOCKED on one criterion, durable private snapshot retention
(§6).** Every other Milestone 2 criterion passes. Nothing was merged or deployed;
the V6 beta is untouched.

## 1. What was built

- **`src/cfb_analytics/v7_market_archive.py`** joins CFBD `/lines` to the verified
  results archive (`research/archive/verified/espn-games.json.gz`; no second
  results database) by game ID. It checks team names (via
  `forecast_ledger.ALIASES`) and final scores, then:
  - selects one provider per game and market (policy v2, §3);
  - computes ATS and over/under (O/U) results, including pushes;
  - builds derived team statistics with a disputed-inclusion sensitivity;
  - validates coverage and quality thresholds;
  - guards against upstream changes and truncated responses;
  - writes both outputs atomically, keeping the last good versions on failure;
  - supports an exact incremental current-season merge;
  - enforces the licensing guard on public output.
- **`refresh.fetch_cfbd_lines`** sits next to the existing CFBD fetch.
- **`.github/workflows/v7-market-backfill.yml`** runs on `v7-development` only.
  Its steps: full tests → aggregate diagnostics → full rebuild →
  byte-identical offline regeneration → incremental equals full → independent
  hand-check and Texas Tech reconciliation → licensing tests → commit of the two
  derived files only.
- **`refresh-data.yml`** gets an isolated current-season step
  (`continue-on-error`, with a warning on failure). It is effective only after a
  future merge to `main`.
- **Public outputs:**
  - `web/public/v7-team-market-history.json`: 138 FBS programs, 1.36 MB
    (89 KB gzipped);
  - `data/v7-market-receipts.json`: SHA-256 hashes, retrieval times and counts.

## 2. Coverage (real backfill, 2016–2025, plus 2026 to date)

All seasons from 2016 to 2025 passed every threshold:
- matched ≥ 99%;
- team names and scores 100%;
- closing spreads ≥ 98%;
- totals ≥ 85%;
- disputed ≤ 5% per market;
- zero suspicious values;
- zero conflicting duplicates.

| Season | Archive | Matched | Spread used (ok + disputed) | Spread disputed | Total used | Total disputed | Opening spread / total | Sole-outlier replacements (spread / total) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | 873 | 873 | 99.2% | 11 | 87.1% | 14 | 0 / 0 | 204 / 0 |
| 2017 | 874 | 874 | 99.9% | 0 | 89.8% | 0 | 0 / 0 | 6 / 0 |
| 2018 | 884 | 884 | 98.3% | 5 | 96.3% | 4 | 0 / 0 | 3 / 7 |
| 2019 | 888 | 888 | 99.2% | 2 | 99.2% | 1 | 0 / 0 | 0 / 0 |
| 2020 | 570 | 568 | 99.8% | 6 | 99.8% | 0 | 0 / 0 | 1 / 0 |
| 2021 | 887 | 887 | 100% | 0 | 100% | 0 | 13 / 12 | 2 / 0 |
| 2022 | 896 | 896 | 99.6% | 0 | 99.6% | 0 | 11 / 11 | 0 / 0 |
| 2023 | 910 | 910 | 99.7% | 12 | 99.7% | 12 | 769 / 516 | 46 / 53 |
| 2024 | 919 | 919 | 98.4% | 7 | 98.3% | 7 | 757 / 203 | 14 / 16 |
| 2025 | 934 | 934 | 100% | 11 | 100% | 3 | 811 / 215 | 12 / 15 |
| 2026 (to date) | 888 | 888 | 93.8% (upcoming games have no line yet) | 4 | 93.8% | 3 | 825 / 767 | 0 / 0 |

**Totals for 2016–2025:** 8,633 of 8,635 archive games matched. Name and score
agreement is 100%.

**Opening values are counted only from the selected provider.** That is why 2021
and 2022 show low counts here: M1 counted any provider. Opening values are
reported, not required.

## 3. Provider policy v2 (evidence-driven amendment to plan §4)

The first real backfill was **correctly rejected** by the unchanged 5% disputed
threshold. Aggregate diagnostics then showed the cause:

| Finding | Detail |
| --- | --- |
| 2016 CFBD `consensus` | Sole outlier in **233 of 249** disputed spreads (34 even named the opposite favourite). |
| DraftKings, 2023–2025 | Same pattern when it was the priority provider: 2023 sole outlier in 46/58 spreads and 51/63 totals; 2024 in 14/21 spreads and 16/23 totals; 2025 in 12/23 spreads and 15/18 totals. |
| Sign-check bug | The `formattedSpread` check misread shared-name prefixes (e.g. "Texas" inside "Texas Tech"). |

**v2 rules.** No line is ever averaged into a selection; medians are used only
for comparison:

1. **Sole-outlier rule.** If the priority provider (consensus or a sportsbook)
   is 3 or more points from the median of 2 or more other providers that agree
   within 3 points, the highest-priority provider of that agreeing group is
   selected. The reason is recorded and counted.
2. **Dispute test.** A game is disputed when the selected value is 3 or more
   points from the median of the remaining providers. The rule's earlier form,
   where any single differing book was enough, flagged games whenever one book
   captured its line at a different time.
3. **Sign check.** It now matches full team names, longest first.

**The thresholds were not changed.** The policy version moved to 2, and every
change is covered by regression tests.

**Documented 2016 Texas Tech cases under v2:**

| Game | Result |
| --- | --- |
| West Virginia (`400869627`) | Consensus −1 replaced by teamrankings +3; Texas Tech ATS **L** |
| Arizona State (`400869100`) | Consensus −5 replaced by teamrankings +1.5; Arizona State ATS **W** |
| Louisiana Tech (`400869359`) | Consensus −12 kept (1.25 from the median); **W** |
| Stephen F. Austin (`400869625`) | Single provider; total has no line |

## 4. ATS and O/U validation and sensitivity

**Validation:**
- **Independent hand-check:** 13 games across 2016, 2020 and 2025, recomputed
  with separate plain code (provider rule, orientation and arithmetic). All
  match. The logs list outcome letters only, no line values.
- **Texas Tech reconciliation:** 2016–2026 overall ATS 73–57–5 and O/U 69–62–1
  equal the sum of its per-season records.
- **Reproducibility:** offline regeneration from the private snapshots is
  byte-identical, and the incremental current-season refresh (2 calls, no
  history download) equals the full rebuild for all 138 teams.

**Sensitivity:**
- **Primary method (unchanged):** disputed games are excluded. ATS games:
  **8,720**.
- **Including disputed games** (deterministic selected provider): **8,771**,
  i.e. +51 games, 0.6%.
- **Teams affected:** 79 (ATS) and 65 (O/U).
- **Largest change in a team's cover rate:** 1.2 percentage points (Sam Houston
  State 19–29 → 20–29; next Georgia 1.1, Jacksonville State 1.0).
- **Texas Tech:** ATS unchanged; O/U 69–62–1 → 71–62–1.

Both the primary and sensitivity counts are published, each with its own
denominator.

## 5. Licensing safeguards (verified)

- **Public file contents:** team keys are limited to counts, W/L/P letters
  (`ats_sequence`, `recent_results`), rounded average cover margins and
  history cover-margin sums.
  - Averages and sums appear only when based on **5 or more** games, so a small
    sample cannot reveal a line.
  - There are **no per-game spreads, totals, cover margins, providers or game
    IDs**.
- **Enforcement:** `assert_public_safe` runs on every build. Tests reject each
  restricted field.
- **Raw data:** raw CFBD responses and per-game selected lines exist only in the
  runner's `$RUNNER_TEMP`. They are not in the repository, artifacts, caches or
  logs.
- **CI output:** logs carry aggregates plus 13 hand-check lines with outcome
  letters.
- **Attribution:** "Data provided by CollegeFootballData.com".
- **Pending:** the CFBD answer on per-game display. Nothing game-level is
  published until it arrives.

## 6. Durable private snapshot retention — **BLOCKED**

- **What exists:**
  - checksummed receipts with upstream-change detection;
  - deterministic regeneration (verified from the runner's private snapshots);
  - last-good preservation;
  - a private gitignored `--cache` for the owner's machine.
- **Why durability is missing:** no **authorized durable private storage**
  exists for this repository's CI.
  - The repository is public.
  - Artifacts and logs of a public repository are public.
  - Actions caches can be restored by fork pull requests.
  - The account's private repositories belong to unrelated projects, and CI
    has no credential for them.

  So snapshots persist only for the duration of a run. Each re-derivation
  re-fetches them (20 calls), and the receipts' hashes prove whether the source
  bytes are unchanged.
- **Owner decision needed (free options):**
  - (a) Create a dedicated private repository, e.g. `cfb-analytics-private-data`,
    and add a fine-grained write token as an Actions secret. The backfill then
    pushes snapshots there.
  - (b) Designate the owner's local machine as the retention location.

  Neither was set up without approval.

## 7. Tests

| Suite | Result |
| --- | --- |
| `pytest` (full) | **613 passed**: 554 pre-existing plus 59 new in `tests/test_v7_market_archive.py` (the committed-archive test now runs against the real file) |
| Real backfill workflow | All steps green (run above) |
| Frontend `npm run build` | Passes. The app source is unchanged; the new public file is copied into `dist` |

The new tests cover:
- ID matching and duplicates;
- identity, aliases and score agreement;
- sign convention, including shared-prefix names;
- ATS and O/U with pushes, pick'em, neutral games and team-perspective
  inversion;
- missing data and suspicious values;
- provider determinism and the sole-outlier rule, including the documented 2016
  cases;
- dispute detection and sensitivity;
- coverage thresholds;
- reproducibility, and incremental equal to full;
- upstream-change and truncation guards;
- no future leakage in the current season;
- the licensing guard, small-sample disclosure and FBS-only publication;
- six refresh-failure modes that preserve the last good outputs.

The 554 existing tests are unchanged and pass. No prediction, simulation, archive
or V6 behaviour was changed.

## 8. Not in scope (unchanged)

No Kalshi retrieval, storage or code. No model-vs-total comparison, intraday
movement, order-book depth or UI. M3 has not started.
