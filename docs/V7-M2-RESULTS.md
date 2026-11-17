# V7 Milestone 2 — Historical Market Archive: results

**Branch:** `v7-development`. **Baseline:** `main` `ec98f28`, plus the approved V7
planning documents (`79ebed1`).
**Verified commit:** `814a43291694576cdbaf9efa2fc8cf76dc9844fb` (workflow and code). CI committed
the derived outputs as `9f9806a` and, after the confirming restore run, as `3cd5b91`; both outputs
differ from earlier ones only in timestamps and the live 2026 regular-season snapshot.
**Verified runs:**
- [43922485394](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43922485394)
  (push): the first save, to an empty private store.
- [43923120836](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43923120836)
  (dispatch, on `9f9806a`): restored the store at the start of the run.

**Determination: CLOSED (2026-11-16). All ten Milestone 2 criteria pass** (§9). Nothing was merged
or deployed; the V6 beta is untouched. Kalshi remains blocked.

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

## 5. Licensing safeguards (updated for CFBD's written permission, see `docs/V7-LICENSING.md`)

**Public outputs:**
- **Team statistics** (`web/public/v7-team-market-history.json`):
  - counts and W/L/P letters;
  - average cover margins and history cover-margin sums, shown only when based
    on 5 or more games;
  - no providers or game IDs.
- **Authorized per-game lines** (`web/public/v7-team-lines/<team>.json`, one file
  per current FBS program): for each game, a closing spread and a closing total
  from **one** selected provider, each with the provider named and a status.
  Each game also carries its date and opponent, home/away/neutral, the score,
  and the ATS and over/under result.
  - There is no combined file, no index and no download link.
  - The files back team and game pages only.

**Never published:**
- opening lines, other providers' values and moneylines;
- disagreement magnitudes;
- raw CFBD responses and private snapshots.

**Enforcement:**
- `assert_team_lines_safe` and `assert_public_safe` run on every build.
- Tests reject unauthorized fields, a line without exactly one named provider,
  duplicate games and extra file keys such as download links.

**Other boundaries:**
- CI logs carry aggregates plus 13 hand-check lines with outcome letters only.
- Attribution ("Data provided by CollegeFootballData.com") and the permission
  note travel with every public file.

## 6. Durable private snapshot retention — **verified**

**Store.** The owner approved Option A: the private GitHub repository
`landrumc16/cfb-analytics-private-data`, reached with the Actions secret `CFBD_SNAPSHOT_TOKEN`
(fine-grained, limited to that repository). The CFBD authorization evidence is kept there privately,
under `licensing/cfbd-betting-lines-authorization/`.

**How the workflow uses it** (`.github/workflows/v7-market-backfill.yml`):
1. **Access and visibility.** It calls the GitHub API with the token. The run fails unless the
   repository is reachable and reports `private: true` with visibility `private`. Raw data is never
   written to a non-private store.
2. **Restore.** It clones the store with the token in the clone URL. A plain clone also works on an
   empty repository. Every snapshot must match both its stored SHA-256 and the public receipt;
   `--accept-upstream-change` never applies to stored bytes.
3. **Rebuild and validate.** The full rebuild, byte-identical offline check, incremental check,
   independent hand-check and licensing tests all run, as in §1.
4. **Save.** Only after full validation does it commit the snapshots and push them to the store.
5. **Durable-restore proof.** It clones the store fresh and regenerates the public outputs offline.
   They must be byte-identical.
6. **Leak scan.** It checks all 140 public files and the public repository's git index for:
   - raw multi-provider fields (`formattedSpread`, opening lines, moneylines, provider arrays);
   - snapshot paths;
   - credential strings;
   - any line value without exactly one named provider.

   Any hit fails the run.

**Real verification:**

| Check | Run 43922485394 (first save) | Run 43923120836 (restore) |
| --- | --- | --- |
| Repository reachable and private | `private=True visibility=private` | same |
| Restored at start of run | 0 snapshots (new repository) | **22 snapshots**, checksums verified against stored meta and public receipts |
| Diagnostics step | 57 s (downloaded from CFBD) | 22 s (history read from the store) |
| Offline regeneration | byte-identical | byte-identical |
| Incremental equals full | 138 teams | 138 teams |
| Saved to private store | 22 snapshots, private commit `91fa039` | 22 snapshots, private commit `d4296b0` (live 2026 snapshot refreshed) |
| Fresh private clone regenerates offline | byte-identical | byte-identical |
| Leak scan | passed | passed |

Every historical (2016–2025) SHA-256 in `data/v7-market-receipts.json` was unchanged by these runs.
Only the live 2026 regular-season snapshot changed, as expected.

**No leakage, verified:**
- Both full job logs were searched:
  - the token pattern appears only as script source (`${TOKEN}`), with 16 masked occurrences
    (`***`) and no token values;
  - raw field names appear only in script source;
  - provider names appear only in aggregate diagnostic counter names;
  - no line values or raw rows are printed.
- Neither run uploaded artifacts (0 artifacts).
- The workflow uses no Actions cache.
- The bot commits touched only:
  - `data/v7-market-receipts.json`;
  - `web/public/v7-team-market-history.json`;
  - `web/public/v7-team-lines/`.
- `private-store/` and `private-store-verify/` are gitignored, and the leak scan confirms that no
  snapshot path is tracked.
- An unauthenticated request for the store returns HTTP 403.

**Security model:**
- The workflow runs only on `v7-development` pushes and manual dispatch, never on `pull_request`, so
  fork workflows cannot read the token.
- Without the token, it falls back to temporary runner storage with a visible warning.

## 7. Tests

| Suite | Result |
| --- | --- |
| `pytest` (full, local at `3cd5b91`) | **628 passed**: 554 pre-existing plus 74 in `tests/test_v7_market_archive.py` |
| Real backfill workflow | All 19 steps green in both runs above |
| PR #33 CI at `814a432` | All checks green except `visual`, the V6 protected-path guard, which fails by design because V7 adds files under protected data paths. Not weakened. |
| `frontend` / `mobile-smoke` | Now passes in CI. "Compare teams" is hidden on prediction cards involving a team the Compare page cannot represent (for example FCS Chattanooga), and the smoke test asserts this, then uses an FBS-vs-FBS card. |

The tests cover:
- ID matching and duplicates;
- identity, aliases and score agreement;
- sign convention, including shared-prefix names;
- ATS and O/U with pushes, pick'em, neutral games and team-perspective inversion;
- missing data and suspicious values;
- provider determinism and the sole-outlier rule, including the documented 2016 cases;
- dispute detection and sensitivity;
- coverage thresholds;
- reproducibility, and incremental equal to full;
- upstream-change and truncation guards;
- no future leakage in the current season;
- the licensing guards and FBS-only publication;
- private-store save, restore, tamper and forged-checksum rejection;
- refresh-failure modes that preserve the last good outputs.

The 554 existing tests are unchanged and pass. No prediction, simulation, archive or V6 behaviour
was changed.

## 8. Not in scope (unchanged)

No Kalshi retrieval, storage or code. No model-vs-total comparison, intraday
movement, order-book depth or UI. M3 has not started.

## 9. Acceptance criteria — final

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Lines matched to the verified archive | ✅ | 8,633 of 8,635 games (2016–2025); 100% name and score agreement (§2) |
| 2 | ATS and O/U implemented and independently tested | ✅ | 13 of 13 independent hand-checks; Texas Tech totals reconcile (§4) |
| 3 | Deterministic, documented provider selection and disputes | ✅ | Policy v2 (§3), regression tests |
| 4 | Reproducible coverage and quality reports | ✅ | Byte-identical offline regeneration, in both runs and from a fresh private clone |
| 5 | Derived team statistics correct | ✅ | 138 FBS programs; incremental equals full; sensitivity published (§4) |
| 6 | No restricted data in public outputs | ✅ | Licensing guards on every build, plus the CI leak scan (§5, §6) |
| 7 | Durable private snapshot retention | ✅ | Real save → fresh clone → offline restore; the second run restored 22 snapshots (§6) |
| 8 | Failed refreshes preserve last-good data | ✅ | Failure-mode tests; atomic writes |
| 9 | Required tests pass | ✅ | 628 Python tests; both backfill runs green; PR #33 green except the by-design `visual` guard |
| 10 | Committed and ready for review, without deployment | ✅ | `v7-development`, draft PR #33 (NOT FOR MERGE); nothing merged or deployed |

## 10. Next: Milestone 3 (not started)

As defined in `docs/V7-ROADMAP.md` (no new plan), M3 is the **comparison and metrics engine**. It
builds on this archive and needs no new data source. It covers:
- home/away/favourite/underdog ATS and O/U splits and cover margins;
- implied probabilities with quote/fee caveats;
- model-market differences, only where the model actually produces a supported output;
- uncertainty and sample-size labelling;
- explainable N/A states.

It is done when there are independent calculation fixtures, push/void/boundary tests, comparability
tests, and no unsupported model-margin or total outputs.

M3 starts only on owner instruction. Kalshi stays blocked pending written authorization.
