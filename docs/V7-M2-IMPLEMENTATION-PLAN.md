# V7 Milestone 2 — Historical Market Archive: implementation plan

**Status:** ready for implementation after the beta review and an explicit owner
instruction to start Milestone 2.
**Inputs:** `docs/V7-ROADMAP.md`; `docs/V7-DATA-FEASIBILITY.md` (verified at
`f505b23`); [CFBD sample run 43865079391](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43865079391).

**Branch rules:**
- Implement on a new branch, `v7-development`, cut from the then-current `main`.
- Nothing reaches `main`, Pages or the beta app without owner approval.

**Scope:**
- **In scope:** CFBD historical spreads and totals; derived ATS and over/under
  (O/U) statistics; provenance and validation.
- **Out of scope:** Kalshi (blocked), model-vs-total, intraday movement,
  order-book depth, any UI (M5) and any new model.

> **Licensing amendment (CFBD written permission, recorded 2026-11-16; see `docs/V7-LICENSING.md`).**
> One provider's closing spread and closing total per FBS game since 2016, provider named, may
> appear in browser JSON backing team and game pages, but never as a standalone dataset, bulk
> download or data feed. The M2 public contract therefore adds per-team files
> `web/public/v7-team-lines/<team>.json`. Opening values, other providers, moneylines, raw responses
> and snapshots stay private. The §3C and §5 statements that "no per-game spreads/totals are
> published" are superseded for these authorized fields only.

> **Implementation amendment (provider policy v2).** The first real backfill stopped at
> the unchanged 5% disputed threshold. Aggregate diagnostics showed priority-provider
> sole outliers: 2016 consensus, and DraftKings in 2023–2025. §4 rules 1 and 4 therefore
> now use a sole-outlier rule and a median dispute test. Publication is limited to
> current FBS programs, the public file is compact, and small-sample cover sums are
> withheld identically in full and incremental builds. See `docs/V7-M2-RESULTS.md` §3.
> The thresholds are unchanged.

## 1. Existing code and data to reuse

| Need | Reuse | Change |
| --- | --- | --- |
| Authoritative games, teams, scores and kickoff times, 2016–2025 | `research/archive/verified/espn-games.json.gz` (keyed by ESPN `game_id`, which equals the CFBD `id`; verified 8,633 of 8,635 matches) | None. It stays the only results source. |
| Current-season games and scores | `data/cfbd-2026-games.json` (via `refresh.py` / `ingestion.normalize_cfbd_games`) | None |
| Team-name aliases | `forecast_ledger.ALIASES` (same map in `pipeline.py` / `report.py`) | Import it; do not add another copy |
| CFBD HTTP pattern and key handling | `refresh.fetch_cfbd_games` (Bearer key from `CFBD_API_KEY`, 45 s timeout) | Add a sibling `fetch_cfbd_lines(year, season_type, key)` |
| Atomic, last-good writes | `refresh.refresh`: write to a `.tmp` file then `replace`; never overwrite on failure | Same pattern for the public output |
| Join, ATS/O-U and scale-fit logic | `scripts/v7_cfbd_lines_sample.py` (verified in CI) | Promote it into the module below. Delete the sample workflow and script in the same pass. |
| Private-cache pattern for CFBD-derived raw data | `scripts/build_v6_foundation.py` `--cache` with `.cache/` gitignored; documented in `research/v6/README.md` | Same approach for raw lines |
| Spread-to-probability conversion | `model.market_home_win_probability` (scale 19.5, validated) | None. Used later in M3/M6 only. |
| Scheduled refresh, commit and Pages deploy | `.github/workflows/refresh-data.yml`, `dashboard.yml`, `scripts/verify_dashboard_bundle.py` | One added step each (§6) |
| Tests | `tests/` (pytest; 554 currently passing) | New `tests/test_v7_market_archive.py` |

No new dependency, backend, database or external service is needed.

## 2. Minimal code changes (complete list)

1. **`src/cfb_analytics/v7_market_archive.py`** (new, about 300 lines). These pure
   functions plus a CLI make up the whole archive:
   - `fetch_season(year, key)`: calls `/lines` for the regular season and the
     postseason. Returns the raw rows plus the SHA-256 of the canonical JSON.
   - `normalize(raw_rows, retrieved_at)`: produces provider-level line records
     (§3A).
   - `join(records, results)`: matches records to archive or current-season games
     by `game_id`. It checks team names (after aliases) and final scores, and
     raises on any mismatch.
   - `select_lines(game_records)`: applies the provider policy (§4) and returns
     the selected-line record with flags.
   - `outcomes(selected, game)`: computes ATS and O/U results.
   - `team_stats(outcomes)`: builds the derived public statistics (§3C).
   - `validate(...)`: applies the acceptance thresholds (§8). Raises
     `ArchiveRejected` with the reason.
   - `main()`: modes `--backfill 2016-2025`, `--season 2026` and `--check`
     (offline re-derivation from the private cache, with a byte-identity check).
2. **`src/cfb_analytics/refresh.py`:** add `fetch_cfbd_lines` next to
   `fetch_cfbd_games`. Existing behaviour stays unchanged.
3. **`tests/test_v7_market_archive.py`** (new): the tests in §7.
4. **`data/v7-market-receipts.json`** (new, committed, public). It contains
   provenance only and no line values (§3B).
5. **`web/public/v7-team-market-history.json`** (new, committed, public). It
   contains derived statistics only (§3C).
6. **Workflows:**
   - Add a "Refresh current-season lines" step to `refresh-data.yml`.
   - Add a manual `v7-market-backfill.yml` (`workflow_dispatch` on
     `v7-development`).
   - Add validation of the new public file to `dashboard.yml` and
     `verify_dashboard_bundle.py`.
   - Delete `.github/workflows/v7-cfbd-lines-sample.yml` and
     `scripts/v7_cfbd_lines_sample.py`.

## 3. Data schema

### A. Private provider-level line record

Never committed, never published, never uploaded as a CI artifact, and never
printed in CI logs beyond aggregates.

```json
{"game_id": "400869627", "season": 2016, "season_type": "regular", "week": 7,
 "provider": "teamrankings", "spread": 3.0, "spread_open": null,
 "total": 82.0, "total_open": null, "formatted_spread": "West Virginia -3",
 "home_moneyline": null, "away_moneyline": null,
 "retrieved_at": "2026-…Z", "source_sha256": "<per season+type response hash>"}
```

- **Sign convention:** `spread` is the **home** spread, where negative means the
  home team is favoured. This is CFBD's convention, verified against archive
  scores; a test enforces it via `formatted_spread` (§7).
- **Storage:** raw responses and these records live only in the runner's
  workspace during a build. The owner can also keep a local, gitignored
  `.cache/v7-cfbd-lines/<season>-<type>.json` for offline `--check`, the same
  pattern as V6.
- **Why there is no persistent raw storage on GitHub:**
  - The repository is public.
  - Artifacts and logs of a public repository are publicly readable.
  - Actions caches can be restored by fork pull-request workflows.
  - A full re-fetch costs only about 20 calls (§6), so the derived and receipt
    files are the durable record.

### B. Public provenance receipt: `data/v7-market-receipts.json`

```json
{"schema_version": 1, "provider_policy_version": 1,
 "source": "CollegeFootballData.com /lines",
 "attribution": "Data provided by CollegeFootballData.com",
 "seasons": {"2016": {"regular": {"retrieved_at": "…", "sha256": "…", "rows": 873},
                      "postseason": {"retrieved_at": "…", "sha256": "…", "rows": 0},
                      "coverage": {"archive_games": 873, "matched": 873, "with_spread": 866,
                                   "with_total": 0, "spread_open": 0, "total_open": 0,
                                   "disputed_spread": 0, "disputed_total": 0, "suspicious": 0,
                                   "excluded_no_line": 7},
                      "selected_provider_counts": {"consensus": 0}}}}
```

The coverage values in this example are illustrative; the implementation writes
the measured counts. Receipts carry hashes and counts only, never line values.

### C. Public derived statistics: `web/public/v7-team-market-history.json`

```json
{"schema_version": 1, "generated_at": "…", "provider_policy_version": 1,
 "attribution": "Data provided by CollegeFootballData.com",
 "seasons": [2016, …, 2026], "current_season_complete": false,
 "teams": {"Texas Tech": {
   "overall":  {"ats": {"w":0,"l":0,"p":0}, "ou": {"o":0,"u":0,"p":0},
                "games": 0, "no_line": 0, "disputed": 0, "avg_cover_margin": 0.0},
   "by_season": {"2016": {"…same shape…"}},
   "home": {"…"}, "away": {"…"}, "neutral": {"…"},
   "favorite": {"…"}, "underdog": {"…"}, "pickem": {"…"},
   "last_n": {"5": {"ats": {"w":0,"l":0,"p":0}}, "10": {"…"}, "20": {"…"}},
   "recent_results": ["W","L","P","…"]}},
 "coverage": {"2016": {"…copy of receipt coverage…"}}}
```

- Values here are illustrative placeholders; the implementation writes computed
  counts.
- **No per-game spread, total or cover margin is published.** A per-game cover
  margin plus the public score would reveal the line itself.
- `recent_results` holds ATS outcome letters (W/L/P) only, most recent first,
  for 20 games at most, labelled by season.
- Averages are rounded to 0.1. All counts carry their denominators.

## 4. Provider-selection policy (version 1; deterministic, recorded per game)

1. **One provider per game per market.** Never average, blend or synthesize a
   consensus. Spread and total are selected independently, because 2016–2019
   `consensus` rows often lack totals. Each selection records `provider` and
   `reason` (`priority`, `fallback_missing_consensus` or
   `fallback_missing_value`).
2. **Priority order** (the first provider with a non-null value wins):
   1. `consensus`
   2. `DraftKings`
   3. `ESPN Bet`
   4. `Bovada`
   5. `William Hill (New Jersey)`
   6. `Caesars`, then `Caesars Sportsbook (Colorado)`, then
      `Caesars (Pennsylvania)`
   7. `teamrankings`
   8. `numberfire`
   9. `SugarHouse`
   10. any other provider, sorted alphabetically

   The order prefers the aggregate first, then the major books with the widest
   recent coverage. It is versioned: any change bumps `provider_policy_version`
   and regenerates everything.
3. **Closing vs. opening:**
   - **Closing** is CFBD's `spread` / `overUnder` from the selected provider.
     For completed games this is that provider's last captured value.
   - **Opening** comes only from the **same** selected provider's `spreadOpen` /
     `overUnderOpen`. It is never taken from another provider, and stays null
     when missing (2016–2020).
   - ATS and O/U results use **closing** values only.
4. **Disagreement:**
   - Compute `max |selected − other provider|` across providers with a value for
     the same market.
   - At **3.0 points or more**, mark the game `disputed` for that market and
     **exclude it from that market's derived statistics**, counting it in
     `disputed` instead.
   - A game with a single provider cannot be checked; it is recorded as
     `single_provider` and included.
5. **Missing or inconsistent values:**
   - No provider with a value: `no_line`, excluded and counted.
   - A non-numeric or non-half-point value, or a sign that contradicts
     `formatted_spread`: `suspicious`, excluded. Any suspicious count above zero
     needs a recorded explanation before acceptance (§8).
6. **What users see** (M5; specified now for consistency):
   - Every statistic shows its denominator and source ("Closing lines:
     CollegeFootballData.com; consensus where available, otherwise named
     sportsbook").
   - Coverage notes show counts of excluded `no_line` and `disputed` games.
   - Where game-level lines are later permitted, the provider name appears
     beside each line.

**Known cases** (from the M1 hand-check; must be reproduced by tests):

| Game | Lines | Expected result |
| --- | --- | --- |
| 2016 Texas Tech vs. West Virginia (`400869627`) | consensus −1; teamrankings +3; numberfire +3 | Selected consensus; disagreement 4.0; `disputed`, excluded |
| 2016 Arizona State vs. Texas Tech (`400869100`) | consensus −5; teamrankings +1.5; numberfire +1 | Disagreement 6.5 (corrected from 6.0 during implementation); `disputed`, excluded |
| 2016 Texas Tech vs. Louisiana Tech (`400869359`) | consensus −12; −11; −10.5 | Disagreement 1.5; included |
| 2016 Texas Tech vs. Stephen F. Austin (`400869625`) | consensus only (−42), no total | `single_provider` spread; total `no_line` |

## 5. Private vs. public boundary

| Private (runner workspace or owner's gitignored `.cache/` only) | Public (committed and deployed) |
| --- | --- |
| Raw `/lines` responses; provider-level records (§3A) | `web/public/v7-team-market-history.json`: derived team statistics, coverage and attribution |
| Selected per-game lines, opening values and disagreement magnitudes | `data/v7-market-receipts.json`: retrieval times, SHA-256 hashes and counts (no values) |
| Detailed validation evidence that lists game-level lines | CI logs and artifacts: aggregates and pass/fail only |
| Model margin vs. closing spread per game (inputs for M6) | M6 later publishes aggregate metrics only |

**Rules:**
- Splitting a complete line archive into many files is **not** treated as
  permission to publish it.
- Until CFBD answers the clarification below, **no historical per-game line
  values** go into any public file.
- A test fails if any public file contains spread or total fields, or more than
  aggregate keys (§7, test 13).

**CFBD clarification (draft for owner review; not sent).** Send it via the
contact address on https://collegefootballdata.com/terms or the CFBD Discord.

> Hello — I run College Football Analytics, a free, no-account fan site hosted on
> GitHub Pages. Because it's static, every JSON file the browser loads can be
> downloaded directly. We plan to publish only **derived** statistics built from
> `/lines`: team ATS and over/under records by season, home/away and
> favourite/underdog splits, coverage counts and attribution. Raw responses stay
> private, and the API key is kept server-side.
>
> Two questions under Sections 4–5 of your Terms:
> 1. Is it acceptable to also show the closing spread and total, with the
>    provider named, on individual game and team-schedule views for past seasons?
> 2. Would publishing those per-game closing values for all FBS games from 2016
>    onward, split by team, count as a "standalone dataset or bulk download"? If
>    so, what scope would you consider reasonable display?
>
> We will attribute "Data provided by CollegeFootballData.com." Thank you.

## 6. Backfill and refresh process

1. **One-time backfill.** Run the manual workflow `v7-market-backfill.yml` on
   `v7-development`, using the existing `CFBD_API_KEY` secret.
   - **Calls:** 2016–2025 × regular/postseason = **20 calls**.
   - **Steps:** normalize → join to the verified archive → select → validate
     (§8) → write the public derived file and receipts atomically → commit those
     two files only.
   - **On failure:** the run fails before writing, leaving the last good
     versions untouched.
2. **Re-derivation without re-download.**
   - **Locally:** `--check` re-derives from the owner's private `.cache/` and
     requires byte-identical public outputs.
   - **In CI:** historical seasons are not re-fetched unless the
     derivation code or policy version changes. Then a new manual backfill is
     run, costing 20 calls again.
3. **Upstream changes.**
   - A backfill compares each season's raw SHA-256 with the committed receipt.
   - **On a mismatch:** the run writes a counts-only diff (rows added, removed or
     changed per season) to the job summary and **fails closed**.
   - Acceptance needs a manual re-run with `accept_upstream_change=true`, which
     the owner reviews.
4. **Current season.** A new step in `refresh-data.yml`, after the existing
   snapshot and report steps:
   - It runs `--season 2026` (2 calls) against `data/cfbd-2026-games.json`.
   - It rebuilds only the 2026 portion and merges it with the committed
     2016–2025 aggregates. Historical per-season aggregates are carried forward
     unchanged; no historical re-fetch.
   - It validates and writes atomically.
   - **Its own exit status is isolated** (`continue-on-error: true` with explicit
     failure annotation). A lines failure must never block the game-results
     refresh, and it keeps the previous market file.
   - Incomplete or upcoming 2026 games are excluded from ATS/O-U until final.
5. **Quota.** Backfill 20 calls plus about 2 per refresh run. Expected under 300
   calls/month in season, within the CFBD free tier of 1,000/month.
6. **Deploy.**
   - `dashboard.yml` copies the public file into `web/dist` and validates its
     schema, coverage and absence of line fields (test 13).
   - This happens on `v7-development` previews only. Production is untouched
     until the V7 release approval.

## 7. Automated validation (pytest; fixtures are tiny and synthetic except the four documented games)

1. **Game ID matching:** every line `game_id` resolves to exactly one
   archive/current game. Unmatched IDs are counted, not silently dropped.
2. **Duplicates:** at most one record per (`game_id`, `provider`); duplicate API
   rows are deduplicated only if identical, otherwise rejected.
3. **Team identity:** CFBD home and away names (after `forecast_ledger.ALIASES`)
   equal the archive's home/away, or the swapped pair, with the spread sign
   flipped. Any other mismatch raises.
4. **Final scores:** CFBD scores, when present, equal archive scores. One
   mismatch rejects the season.
5. **Spread sign convention:**
   - The fixture checks the favoured team in `formatted_spread` against the
     sign: negative home spread means the home team is named.
   - The 2016 Texas Tech vs. Kansas fixture (home −27.5, won 55–19) yields home
     cover +8.5.
6. **ATS outcomes:** `margin + spread` greater than 0 is a home cover, less than
   0 an away cover, and exactly 0 a push. Fixtures cover a half-point win, a
   push on an integer spread, a pick'em (spread 0: no favourite), a neutral
   site, and team-perspective inversion (an away team's W equals the home team's
   L).
7. **O/U outcomes:** `total_points − total` greater than 0 is over, less than 0
   under, 0 a push, including an integer-total push fixture.
8. **Missing data:** no providers gives `no_line`; spread present with total
   missing gives an independent selection; null opening values stay null and are
   never substituted from another provider.
9. **Provider selection:**
   - The priority order is deterministic regardless of API row order (shuffled
     input gives an identical result).
   - The fallback reason is recorded.
   - The four §4 documented games produce exactly the listed outcomes.
10. **Suspicious values:**
    - Rejected: absolute spread above 70, total outside 20–110, non-half-point
      values, |open − close| above 21, and a sign contradicting
      `formatted_spread`.
    - Each is flagged `suspicious` and excluded.
11. **Coverage by season:** the coverage counts reconcile exactly
    (`archive_games = matched + unmatched`;
    `matched = included + no_line + disputed + suspicious`), and the §8
    thresholds are enforced.
12. **Reproducibility:** the same raw input yields byte-identical public outputs
    (sorted keys, fixed rounding, no wall-clock time except `generated_at`,
    which is taken from the receipts).
13. **Licensing guard:**
    - Public JSON contains no `spread`, `total`, `open`, `line`, `moneyline` or
      `cover_margin` keys at game level, and no per-game arrays except
      `recent_results` W/L/P letters.
    - No file under `web/public/` exceeds the aggregate schema.
    - CI logs print no per-game values.
14. **Provenance:** every season in the public file has a receipt with
    `retrieved_at`, `sha256`, row counts and `provider_policy_version`.
15. **Fail-safe writes:** simulated HTTP 503, timeout, an empty list, a truncated
    season (rows below 90% of the receipt), score mismatch, threshold failure
    and a hash change without acceptance each leave the previous public file and
    receipts byte-identical, with a non-zero exit. This reuses the
    `test_refresh.py` pattern.
16. **No regression:** the existing 554 tests still pass. No change to model,
    report, CFP or production web outputs.

## 8. Data-quality acceptance thresholds (per completed season, 2016–2025)

| Check | Threshold | M1 observed |
| --- | --- | --- |
| Archive games matched by ID | ≥ 99.0% | 99.98% overall (2020: 568/570) |
| Team names agree | 100% of matched | 100% |
| Final scores agree | 100% of matched | 100% |
| Closing spread available | ≥ 98.0% of matched | 98.3%–100% |
| Closing total available (after fallback) | ≥ 85.0% of matched | 87%–100% (consensus only: lower in 2016–2019) |
| Opening values | Reported only, no threshold | 0% (2016–2020); 91.7–100% (2021–2025) |
| Disputed (≥ 3.0 pts) per market | ≤ 5.0% of matched; above that, stop and review policy | To be measured at backfill |
| Suspicious values | 0 unexplained | To be measured at backfill |
| Duplicate conflicting rows | 0 | Not observed |
| Row count vs. prior receipt | ≥ 90% (truncation guard) | — |

Current season: the same identity, score and value checks apply. Coverage
thresholds apply only to completed weeks.

## 9. Milestone 2 definition of finished

1. `v7_market_archive.py`, `fetch_cfbd_lines`, both workflow changes and
   `tests/test_v7_market_archive.py` are merged into `v7-development`. All §7
   tests and the existing suite pass in CI.
2. One real backfill (20 calls) completes and passes every §8 threshold. The
   receipts and the derived public file are committed from that run.
3. A real current-season refresh run updates 2026 statistics without
   re-fetching history. The simulated failure cases in test 15 are proven not to
   overwrite.
4. Hand-check: at least 10 games across 2016, 2020 and 2025, including the four
   §4 cases. Selected provider, ATS and O/U results are recomputed by hand from
   archive scores and the private records, with exact agreement recorded in the
   PR. Only games and outcomes are listed, not line values.
5. Texas Tech's derived ATS and O/U totals are reconciled against the sum of
   its per-season records.
6. The licensing guard (test 13) passes, and no raw or line-level data appears
   in the repository, artifacts or logs.
7. The coverage report is published (`coverage` blocks), and missing history is
   explicitly N/A.
8. No production change. The V6 app, beta, consent and analytics are untouched.
   The sample workflow and script are removed.

## 10. Blockers

- **None blocking Milestone 2 implementation.**
- **CFBD clarification (pending owner send):** affects only *displaying*
  historical per-game lines (M5). M2 publishes derived statistics only.
- **Kalshi authorization:** affects Market Watch (M4) only. No Kalshi retrieval,
  storage or code in M2.
- **Sequencing:** implementation starts only after the beta review and an
  explicit owner instruction.
