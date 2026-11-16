# Version 7 release acceptance (Milestones 5–7)

**Branch:** `v7-development`. **PR:** #33 (draft, NOT FOR MERGE until the owner approves).
**Roadmap:** `docs/V7-ROADMAP.md`, including the 2026-11-16 market-analysis refocus amendment.

Nothing has been merged or deployed. V6 production and the public beta are unchanged. PR #34
(Rankings fix) contains no V7 files.

| Item | Value |
| --- | --- |
| Verified code commit | `fdc6138ef96f7e8c496d44c1a46340e7b4db9e3a`: every CI check green, including `visual` |
| Follow-up commit `d2acaac` | CI-regenerated outputs; differs only in timestamps and input fingerprints |
| Final head | This document's commit, which adds documentation only. Its CI results are in the owner report |

## Milestone 5: user experience (calculator in Compare & What If)

| Requirement | Evidence |
| --- | --- |
| Integrated into the existing matchup experience | Renders under the model's projected winner; the parity test shows the rest of the Compare page unchanged |
| Published forecasts distinguished from hypothetical matchups | "Published forecast" badge with the week, versus "Hypothetical matchup" with an explanation; both asserted in the browser |
| Correct team perspectives | Keyboard team switch reverses the spread (−6.5 → +6.5), the probability (41.3 → 58.7) and the model figures; differences match independent arithmetic |
| Understandable explanations | One plain-English sentence per comparison; exact wording is unit-tested and checked for betting language |
| Mobile and responsive | 320, 375, 390, 430, 768 and 1536px, with no horizontal overflow. 320px is the WCAG 1.4.10 reflow width; 200% zoom of a 768px window is a 384px layout |
| Accessible | Labelled inputs, a radio group, `aria-invalid`, polite live regions, 44px targets, a visible focus outline, and WCAG AA contrast (≥4.5:1) for every calculator text element |
| Empty, invalid and missing states | Empty inputs show nothing; invalid entries show inline messages; a missing model output shows "Model prediction unavailable" with no estimate |
| Privacy | No entered value appears in any request, storage or URL, checked at every width |

## Milestone 6: historical validation (frozen, reproducible)

The module is `src/cfb_analytics/v7_validation.py`; its output is
`research/v7/historical-validation.json`.

**Reproducibility:**
- The output holds aggregates only and passes the licensing guard.
- It records the SHA-256 of every input.
- It uses a 10,000-resample paired bootstrap with a fixed seed.
- `--check` gives byte-identical output, locally and in CI.

### Findings

**1. Archive integrity.**
- All **17,599** published team-game rows were re-joined independently to the verified results
  sources (the 2016–2025 ESPN-origin archive and the 2026 CFBD snapshot), and every ATS and O/U
  letter was recomputed.
- Result: **0** missing games, **0** identity, score or venue mismatches and **0** letter mismatches.

**2. National checks** (each game once, 2016–2026). These describe the archive; they are not
strategies.

| Check | Rate | 95% interval | Games |
| --- | --- | --- | --- |
| Favourite covered | 49.5% | 48.5–50.5% | 9,101 |
| Home team covered | 49.8% | 48.7–50.8% | 8,489 |
| Over | 49.3% | 48.3–50.3% | 8,981 |

All three are consistent with an efficient closing market. Separately, the spread-implied
probability is well calibrated across 9,273 games (M3).

**3. Model vs market on identical games.** This uses only forecasts recorded before kickoff:
125 completed games in 2026 Weeks 10–11, 65 of them independently verified.

| Population | Model Brier | Market Brier | 50/50 Brier | Model − market Brier (95% CI) | Margin MAE (model / market) |
| --- | --- | --- | --- | --- | --- |
| All authentic (125) | 0.2075 | 0.1995 | 0.25 | +0.008 (−0.009 to +0.025) | 13.67 / 13.18 points |
| Verified (65) | 0.2114 | 0.1923 | 0.25 | +0.019 (−0.002 to +0.042) | 13.23 / 12.23 points |

- **Model vs market accuracy:** inconclusive. The market's closing spread scored slightly better,
  but the Brier interval includes zero for both populations.
- **Model vs the 50/50 baseline:** both the model and the market beat it.
- **Margin error:** on the verified cohort the market's margin error was lower (interval
  0.2–1.8 points).
- **Disagreement:** there is no evidence that model–market disagreement carried information beyond
  the market.
  - The signed residual toward the model is +0.048, with an interval of −0.029 to +0.126 that
    includes zero.
  - In the 21 games where the two favourites differed, the model's favourite won 10 (48%).
- **Independent cross-check:** the verified-cohort model figures (Brier 0.2114, 64.6% correct
  winners) reproduce the separate V5 evaluator exactly (0.21139, 42 of 65).

### Limitations (also stored in the output)

- No model forecasts were archived before kickoff for 2016–2025, so there is no historical
  model-vs-market evaluation. Retrospective replays are not used.
- 125 games is a small sample, so week-to-week stability cannot be established.
- The model forecasts were recorded a median of about 151 hours before kickoff, while the closing
  spread reflects later information.
- The model produces no totals, so totals are evaluated only descriptively.
- Nothing here is evidence of a profitable betting strategy; bookmaker margins are not modelled.

## Milestone 7: release acceptance

### Checks

**Local (data staged as CI stages it):**

| Check | Result |
| --- | --- |
| `pytest` | 695 passed |
| `analytics-unit` (privacy, consent, DNT/GPC) | PASS, 7 cases |
| `market-calculator-unit` | PASS |
| `historical-publication` and `v6-scenarios` | PASS (Python/browser parity exact) |
| `mobile-smoke`: five widths and Android Chrome-emulated PWA install, update, offline and recovery | PASS |
| `editorial-home` | PASS |
| `v6-browser`: exact cross-page context and scenario reset, no page errors | PASS |
| `adversarial-reliability` | PASS |
| `market-calculator` | PASS, six widths and the missing-model case |
| `verify_v5_pregame_archive` | 65 games, Brier 0.21139, unchanged |
| Production build and `verify_dashboard_bundle.py` | PASS |
| Before/after editorial parity (`editorial-polish.mjs`) | PASS: navigation, favourites, rankings, profile and program metrics, matchup probabilities, verified scores, research and scenarios identical at five widths |

**CI at `fdc6138`:**
- All jobs green: `visual`, `frontend`, `pytest`, `python`, `python-tests`, `regression`, both
  `historical`, `dashboard`, both `dashboard-build`, and `backfill`. `refresh-evidence` is skipped,
  as it is on every PR.
- Backfill run 43955128866:
  - checked that the private store is reachable and private;
  - restored 22 snapshots and rebuilt with byte-identical output;
  - confirmed the incremental rebuild equals the full rebuild for 138 teams;
  - regenerated the M3 metrics and M6 validation byte-identically;
  - passed 126 licensing and output tests;
  - re-saved the store and rebuilt identically from a fresh clone;
  - passed the leak scan (279 public files) with no credential strings in the log.

### Licensing and privacy

- **Published line data:** one named provider's closing spread and total per game, in per-team files
  only.
- **Aggregate files:** no lines, providers or game IDs.
- **Raw data:** multi-provider snapshots stay in the private repository.
- **Market data:** no Kalshi or third-party market data.
- **Calculator input:** entered numbers never leave the page.

### Data integrity and freshness

- **Verified archive:** unchanged.
- **Pregame forecasts:** the 65-game cohort is unchanged.
- **Season report:** `main`'s latest refresh (2026-11-16 00:42 UTC) is included; `main` has no newer
  commits.
- **Current-season lines:** re-fetched in every backfill (latest 2026-11-16).
- **Coverage:** Week 12 is unplayed, with the first kickoff on November 21.

### V6 preserved

- No V6 behaviour changed: the parity test passes and the committed V6 scenario input is
  byte-identical to `main`.
- The only app-source change is the calculator in `main.tsx`, `MarketCalculator.tsx`,
  `marketCalculator.ts` and `style.css`.

### The `visual` guard: scoped release mechanism

- **What changed:** `.github/workflows/editorial-polish.yml` now calls
  `scripts/verify_protected_changes.py` instead of a bare `git diff --exit-code`.
- **Every other branch:** still requires protected paths to be byte-identical to the merge base.
- **The one exception:** `.github/release-manifests/v7-protected-changes.json` applies only to
  **same-repository pull requests whose head branch is `v7-development`**. It allows:
  - additions of exactly the listed V7 files, plus `<slug>.json` files directly inside the two
    listed V7 folders;
  - edits to `src/cfb_analytics/refresh.py`, and only edits that add lines.

  Deletions, renames, other modifications, nested paths and non-JSON shapes still fail.
- **Tests:** `tests/test_protected_guard.py` (15 tests) covers these rules, including forks and other
  branches.
- **After the release:** remove the manifest once V7 is merged.

## Release readiness

- **Status:** every Milestone 5–7 criterion is met. There are no open release blockers.
- **PR #33:** ready for the owner's review and approval. Merge and deployment happen only on
  explicit approval.
- **Unchanged:** Kalshi stays blocked, and no V7.1 or new roadmap is planned.
