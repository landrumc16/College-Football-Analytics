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

## Information architecture and Market Analysis experience (2026-11-16 owner direction)

**Navigation:**
- The bottom bar is **Home | Rankings | Teams | Playoffs | Market**.
- **Research & Data** is the first item in the top Menu. It opens the unchanged Research destination
  with all five sections.

**One home for the calculator.** `Market` opens the Market Analysis page, the only place the
calculator appears. The page is laid out in order:
1. A **game picker**, pre-selected to the soonest upcoming FBS-vs-FBS game with a published
   forecast.
2. The **calculator**, with spread, prediction-market probability and American moneyline. Results
   update as you type, each with a headline, model value, entered value, difference and sentence.
3. **Historical ATS and over/under records** for both teams: collapsed, and fetched only when opened.

**Links instead of copies:**
- **Homepage:** one compact "Market Analysis" card with an **Open calculator** button, visible in the
  first phone screen.
- **Game Predictions:** each FBS-vs-FBS card has a **Market analysis** button that opens that game.
- **Compare & What If:** the embedded calculator is removed and replaced by "Compare this matchup with
  a market line in Market Analysis". The matchup is carried in memory, either as its scheduled game
  or, for an unscheduled pairing or venue, as a game labelled "Your matchup (hypothetical)".

**Clear conventions:**
- Numbered steps: "1. Analyze for" (large team pills), then "2. Type a market number".
- Spread examples are written in the selected team's name.
- A **±** button covers phone decimal keypads that have no minus key.
- Provenance is shown as a "Published forecast" or "Hypothetical matchup" badge.

**URLs and privacy:**
- Hash routing (`#/market`, `#/compare`, `#/research`, …) gives deep links and browser Back/Forward.
- Only the view name is in the URL. Matchups and entered numbers are never in URLs, storage, requests
  or analytics; the analytics allow-list ignores the `market` view.

**Content placement review.** Each substantial feature has one authoritative location:

| Feature | Authoritative location | Elsewhere |
| --- | --- | --- |
| Market Analysis calculator and ATS/O-U history | Market | Links from Home, Game Predictions and Compare |
| Research & Data | Research | Opened from the menu |
| Team profile, schedule and history | Teams → Team Profiles | — |
| Poll comparisons | Rankings | — |
| Playoff projections and scenarios | Playoffs | — |

Compare & What If keeps its collapsed side-by-side report cards and history, which are its purpose
(comparing two programs) rather than a copy. No unrelated content was moved.

**Evidence:**
- **`web/tests/market-analysis.mjs`** at 375, 390, 430, 768 and 1536px checks:
  - the entry card sits in the first screen;
  - one tap opens a published game;
  - typing plus ± produces an instant result with a headline;
  - switching teams reverses the result;
  - changing games resets entries and re-labels provenance;
  - history is lazy-loaded and matches the published metrics;
  - Compare's link and prediction cards transfer the right matchup;
  - there is no overflow and no entered value leaks.

  At 390 and 1536px it also checks:
  - the five-item bar and Market `aria-current`;
  - menu → Research & Data, with the menu closing afterwards;
  - Back/Back/Forward;
  - deep links `#/market`, `#/research`, `#/compare`, `#/cfp`, and an unknown hash falling back to
    Home;
  - the homepage never embeds the calculator.
- **`web/tests/market-calculator.mjs`** at six widths now reaches the calculator only through
  Compare's link. It covers published and hypothetical transfer, Back to Compare with the matchup
  intact, contrast, focus, invalid input, the missing model and privacy.
- **Updated tests:** the five V6 browser tests that referenced the old bar (`mobile-smoke`,
  `editorial-home`, `v6-browser`, `adversarial-reliability`, `editorial-polish`) now assert the new
  bar and reach Research through the menu.
  - The before/after parity test still requires every visible metric and behaviour to be identical;
    only the navigation list differs, and each phase asserts its own.
  - `adversarial-reliability` now checks recovery on the same view after reload, which deep links
    preserve, and then on Home.
- **Screenshots** from the running app are in `docs/evidence/v7-market-analysis/`: the home entry
  card, the Market page at 390, 768 and 1536px, and the menu with Research & Data.
- **Guard:** the two reviewed protected-file edits (`Navigation.tsx`, `EditorialHome.tsx`) are pinned
  in the release manifest by exact SHA-256. Any further edit fails the `visual` guard.

## PR #34 production verification and V7 integration (2026-11-17)

**PR #34 in production:**
- **Merge:** commit `efecd970daf60cd2c53b368faca3c7aa2d1689d4`.
- **Deploy:** run [43984190997](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43984190997)
  succeeded, including every post-deploy production step:
  - the Pages smoke test;
  - `mobile-smoke.mjs` against the live URL at 375, 390, 430, 768 and 1536px;
  - Android Chrome-emulated install, update, offline and recovery;
  - PostHog live verification.
- **Live bundle:** `assets/index-DX_JGHT2.js` contains Poll Rankings and the FCS Compare guard. It has
  no "Coaches Poll" tab and no V7 code.
- **Independent live check** (Chromium through the session proxy, TLS verified), at five widths:
  - Poll Rankings shows all 25 union teams;
  - the AP header sets `aria-sort="ascending"` with ▲;
  - in Team Stock Watch, the Texas Tech selection renders directly below the filters while the list
    stays visible;
  - no overflow and no page errors.
- **Not visible live:** this week's AP and Coaches polls contain identical teams with no ties, so
  T-n and NR rows cannot appear in production right now. They are covered by the fixture test
  `poll-rankings.mjs`, which passed in CI.
- **Screenshots:** `docs/evidence/pr34-production/`.
- **Earlier deploy failures:** the refresh-triggered dashboard deploys that failed on 2026-11-16 all
  stopped at the FCS "Prediction-to-Compare" smoke assertion that PR #34 fixed. The first deploy after
  the merge passed.

**Integration.** `main` (`efecd97`) was merged into `v7-development`:
- The seven rehearsed hunks were resolved as documented.
- The per-release guard script and workflow step were taken from `main`.
- V7's `Navigation.tsx` pin was re-set to `8aa30905d3278b171123af2e4fb683660d18cb34e6a609d4bb258654a044991a`,
  verified against the merged file.
- PR #34's superseded manifest and its manifest-specific test were removed. Only the V7 manifest
  remains, and it is to be removed after the V7 merge.

**Release-candidate acceptance (local):**

| Check | Result |
| --- | --- |
| `pytest` | 698 passed |
| V7 metrics and validation `--check` | Byte-identical |
| Production build and bundle check | Pass |
| Calculator and privacy unit tests, `historical-publication`, `v6-scenarios` | Pass |
| `poll-rankings`, `market-analysis`, `market-calculator`, `editorial-home`, `v6-browser` | Pass |
| `adversarial-reliability` | Pass, 0 failures |
| `mobile-smoke`, including the Android PWA | Pass |
| Before/after editorial parity | Pass |

**CI on the integrated code** (`4d53090`):
- Every check is green, including `visual`. The guard approved only the two pinned files and the
  listed V7 additions.
- Dispatched backfill [43986080441](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43986080441):
  - private store confirmed private, 22 snapshots restored;
  - byte-identical rebuild, and incremental equals full for 138 teams;
  - metrics and validation byte-identical, with 126 licensing and output tests passing;
  - re-saved, and a fresh private clone rebuilt identically;
  - leak scan passed on 279 public files.
- Its bot commit `30d7382` changed only timestamps, the two input fingerprints and the live 2026
  snapshot's receipt hash.

**The release candidate is this document's commit,** verified by its own CI run.

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

## Release record and closeout (2026-11-18)

### Releases (owner-merged)
| Release | PR | Merged head | Merge commit on `main` | Merged (UTC) |
|---|---|---|---|---|
| Rankings usability (Option A scoped exception) | #34 | `e4c1cd0` | `efecd97` | 2026-11-17 00:01 |
| Version 7 market analysis | #33 | `638835b` | `5147b4b` | 2026-11-17 00:59 |

**Production deployment**
- **Rankings:** "Build and publish analytics dashboard" run 382 deployed `efecd97` (success).
- **Version 7:** push run 383 was cancelled by design (superseded). Run 384, triggered by the data refresh at `0cc6f9e`, deployed V7 (success).

**Later owner-merged production changes (not part of the V7 scope):**
- #36 Market usability, `c72801f`;
- #38 Team strength, `474c72d`;
- #39 Shared school search, `f3ea70b`;
- #40 Week 12 poll fix, `195b21a`.

**Production verification at `195b21a`** (2026-11-18, publish run 392 and Python tests run 2006, both success):
- the published-dashboard smoke test passed;
- live desktop, mobile and PWA journeys passed;
- consented production analytics with excluded test traffic passed;
- the V7 market files (`v7-market-metrics.json`, `v7-team-market-history.json`) are served live.

**Observation:** publish run 389 (2026-11-17 23:19, after a scheduled refresh) failed its post-deploy smoke test with "Deployed report differs from the validated build artifact". Runs 390, 391 and 392 passed the same check, which is consistent with a transient stale read of the newly deployed report. No regression is outstanding.

### Closeout
- **Release manifest removed.** The V7 release manifest has been removed, so `.github/release-manifests/` is now empty. `scripts/verify_protected_changes.py` therefore applies the strict byte-identical guard to every branch. The mechanism is kept for a future owner-approved release; any new manifest must again be removed after merge.
- **Tests updated.** `tests/test_protected_guard.py` now tests the mechanism with a fixture copy of the reviewed V7 manifest, and asserts that no manifest remains and every branch is strict. It also confirms that production still carries exactly the reviewed V7 navigation (`Navigation.tsx`, `EditorialHome.tsx` SHA-256 pins). Any future edit to these protected files needs a new review.
- **Version 7 is complete and formally closed** once this closeout change is merged with owner approval. Kalshi stays blocked, and no V7.1 is planned.
