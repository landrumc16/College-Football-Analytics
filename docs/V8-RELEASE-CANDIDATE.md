# Version 8 release candidate: Offense & Defense intelligence

**Status:** release candidate on `v8-development`, with the owner's final mobile refinements and the release manifest. It is **not** merged or deployed. Merging and challenger
promotion each need explicit owner approval.

**Baseline:** `main` at `7dd7b0c` (after PR #41). The roadmap is `docs/V8-ROADMAP.md` (approved at `1a742cc`),
and the starting issue is #42.

## Outcome

| Area | Result |
| --- | --- |
| Offense & defense profiles | Every FBS team (138 in 2026) has three views: traditional, power-opponent and opponent-adjusted. Each has ranks, sample sizes, uncertainty, situational splits, recent form and consistency |
| Matchup intelligence | Phase-by-phase edges from the same additive model as the opponent adjustment, with plain-language explanations. These are descriptive only |
| Challenger forecast model | Built and evaluated against pre-registered gates. **It fails the gates, so the incumbent is retained.** Published forecasts are unchanged |
| Production safety | No protected file is modified. Forecasts, rankings, CFP, Market, favourites, school search, PWA and analytics are unchanged |

## M1: sources and coverage

**Source:** the CollegeFootballData API (`/teams/fbs`, `/games`, `/drives`, `/plays`), using the existing
`CFBD_API_KEY`.

**Where the data lives:**
- **Raw responses:** kept only in the owner's private snapshot repository.
- **Public files:** only derived per team-game *counts* are committed (`research/v8/team-games/{season}.json.gz`).
- **Checks:** the workflow re-derives offline and must match byte-for-byte. A leak scan rejects play text,
  wallclock times or credentials.

**Acquisition and membership:**
- **Cost:** acquiring 2016–2026 took 230 API calls (run 44538752179).
- **Membership:** `research/v8/fbs-membership.json` records FBS membership by season (128 programs in 2016, 138
  in 2026). This matches the V6 coverage table.

**Coverage:**

| Season | Completed FBS games | With play-by-play | With drives | Coverage |
|---|---:|---:|---:|---:|
| 2016 | 873 | 857 | 857 | 98.2% |
| 2017 | 874 | 869 | 869 | 99.4% |
| 2018 | 884 | 881 | 881 | 99.7% |
| 2019 | 888 | 887 | 887 | 99.9% |
| 2020 | 568 | 568 | 568 | 100.0% |
| 2021 | 887 | 887 | 887 | 100.0% |
| 2022 | 896 | 896 | 896 | 100.0% |
| 2023 | 910 | 910 | 910 | 100.0% |
| 2024 | 919 | 919 | 919 | 100.0% |
| 2025 | 934 | 934 | 934 | 100.0% |
| 2026 (to date) | 757 | 757 | 757 | 100.0% |

**Inputs not available, shown as N/A and never inferred:**
- **Quarterback starters, rotations and injuries:** no pregame-timestamped source was acquired.
- **Travel and altitude:** no venue coordinates are available.
- **Coaching and coordinator changes:** the V6 records lack verified publication cutoffs.

## M2: definitions

**Scrimmage plays:** run, pass and fumble play types on downs 1–4. Penalties, kicks, timeouts and period markers
are excluded, and sacks count as dropbacks.

**Play measures:**
- **Success:** a play gains 50% of the distance on 1st down, 70% on 2nd, or 100% on 3rd and 4th. Touchdowns
  succeed and turnovers fail.
- **Explosive:** a run of 10+ yards or a pass of 20+ yards.
- **Expected points added:** the provider's per-play value.

**Excluded or limited:**
- **Garbage time:** efficiency measures exclude plays when the score margin is more than 38 (Q2), 28 (Q3) or
  22 (Q4). Scoring measures use full games.

**Drive and situational measures:**
- **Points per drive:** points scored on the drive, from the provider's score at the start and end of each drive.
- **Red-zone trip:** any drive that reaches the opponent's 20.
- **Third down:** conversions on the play itself only (penalty first downs are not in the data).
- **Close-late:** 4th quarter or overtime with a margin of 8 points or fewer.

**The three views:**

| View | Definition |
| --- | --- |
| Traditional | All games played. FCS games are included, and their count is shown |
| Power Four only | Only games against ACC, Big Ten, Big 12, SEC and Notre Dame opponents (Pac-12 is included through 2023). Shown for power teams only, with a game count. This is a competition filter, not a strength rating |
| Opponent-adjusted | A weighted ridge fit of each game: value = league mean + offense + defense + home field, solved jointly so schedule strength counts once. Shrinkage priors are listed per metric in `v8_stats.METRICS`. FCS games are excluded from the fit. Standard errors are shown as ± 90% bands |

**Trends and volatility:**
- **Trend:** the last four games against earlier games, using opponent-adjusted game values. A trend is labelled
  improving or declining only beyond 1.645 standard errors.
- **Volatility:** the standard deviation of opponent-adjusted game values, requiring 5 or more games.

**Tests** (`tests/test_v8_sources.py`, `tests/test_v8_stats.py`):
- hand-computed arithmetic;
- garbage-time thresholds;
- membership transitions (Pac-12 2023 vs 2024, BYU, Notre Dame);
- exclusion of FCS teams;
- small-sample shrinkage;
- ties;
- no future leakage;
- reproducibility;
- schedule-strength recovery in a synthetic league.

**Spot checks:**
- The 2026 league averages are realistic: 41.6% success rate, 5.82 yards per play, 2.13 points per drive and a
  39% third-down rate.
- North Dakota State and Sacramento State correctly appear as FBS teams in 2026.

## M3: the product

**Where it lives:** one destination, **Teams → Offense & Defense** (`#/stats`), added from `main.tsx`.
`Navigation.tsx` is unchanged.

**Entry points:**
- Team Profile, via an "Offense & Defense" button;
- Rankings, via "Offense and defense rankings";
- Compare, via "See how these offenses and defenses match up".

**Mobile refinements** (owner review):
- **Shorter introduction:** a one-line description of the selected view, with the full definitions under "How to read
  these numbers" (ranks, the ± 90% range with an example, samples, and descriptive versus predictive).
- **Readable matchups:** the strongest two or three edges come first as cards. Each card names who benefits, the
  expected value against the national average, and a plain explanation built from both units' adjusted values. All
  matchup factors sit behind an expander.
- **Tables:** they fit without sideways scrolling at every tested width. CI enforces this.

**Final mobile polish** (second owner review):
- **Matchup cards:** a "Team defensive/offensive advantage" heading, the statistic, the expected value against the
  national average, and one short sentence. The full calculation sits under "How this is calculated" on each card.
  Calculations and thresholds are unchanged.
- **Less scrolling:**
  - **Page layout:** jump links (Statistics, Matchup, Recent form, Leaders, Team Profile), a compact summary row, and
    the matchup section placed before recent form.
  - **Statistics tables:** scoring and efficiency rows are always visible; running, passing and situational detail
    sits in an expander.
  - **National leaders:** collapsed on phones and opened directly from Rankings.
  - **Result at 390px:** the page is 8,004px → 4,153px, and the matchup section starts at 1,913px instead of
    4,343px.
- **Readability:** text is at least 12px (only the uppercase column labels are 12), ranges and ranks are 13px,
  ± ranges sit under their values, and every control is a 44px touch target. No table or page overflows at
  375–1536px.
- **Bottom navigation:** the viewport does not use `viewport-fit=cover`, so phones keep content out of the
  home-indicator and gesture areas, and the existing `env(safe-area-inset-bottom)` padding is a fallback. In
  emulation, the fixed bar never covers the end of the page (this is tested). It has not been checked on a physical
  device.

**Data file:** `web/public/v8-team-stats.json` (421 KB, about 112 KB gzipped). It is generated by
`cfb_analytics.v8_publish`, and CI checks that it regenerates exactly.

**Tests:**
- **Browser:** `web/tests/offense-defense.mjs` covers 375, 390, 430, 768 and 1536px, keyboard use, contrast,
  sideways scrolling, every entry point and the missing-data state.
- **Helpers:** `web/tests/v8-stats-unit.mjs`.

## M4–M6: challenger and evaluation

**Protocol:** `research/v8/evaluation-protocol.json` was committed (`6709b35`) **before any results**.

**Baseline:** a labelled retrospective replay of the incumbent's own rating method. Each season's prior is the
previous season's final rating.

**Challenger:** a ridge margin model built on that baseline. It adds:
- as-of opponent-adjusted matchup features (efficiency, scoring, run and pass, explosive plays, situational);
- trend;
- volatility;
- vulnerability interactions;
- rest.

**Training:** walk-forward, using only earlier seasons. Every feature is built from games before the week. The
frozen feature snapshot is `research/v8/challenger-features.json.gz`.

### Results (`research/v8/challenger-evaluation.json`)

**Overall** (4,537 games, 2017–2025 excluding 2020):

| Measure | Challenger | Incumbent-method replay |
| --- | --- | --- |
| Brier | 0.1862 | 0.1874 |
| Accuracy | 71.2% | 70.9% |
| Margin MAE | 12.72 | 12.77 |

**Pre-registered gates:**

| Gate | Required | Full model | Reduced model (trend only) |
| --- | --- | --- | --- |
| Pooled Brier improvement | ≥ 2% | 0.62% | 0.34% |
| Brier difference CI95 upper bound | < 0 | +0.0017 | +0.0004 |
| Seasons improved | ≥ 6 of 8 | 5 of 8 | 5 of 8 |
| Log loss | not worse | pass | pass |
| Calibration slope | 0.9–1.1 | 0.95 | 0.95 |

**Verdict: retain the incumbent.**

**Where it helps:**
- **By season:** 2021–2024 each improve by 2.0–3.4%. 2017 is 4.1% worse because only 2016 was available for
  training, and 2025 is 1.5% worse.
- **By game type:** games between two power teams improve by 2.5%. Weeks 1–6 are 1.8% worse.

**Ablation:** removing most single groups lowers held-out Brier, which shows overfitting from correlated inputs.

**Exploratory analysis** (post hoc, not used for gates): efficiency + volatility was selected on 2018–2021 and then
tested on 2022–2025.
- **Result:** Brier 0.1853 vs 0.1874 (+1.1%), with a CI of [−0.0040, −0.0003].
- **Reading:** a small, consistent gain, but below the 2% gate.

**Authentic 2026** (125 FBS games with incumbent probabilities recorded before kickoff):

| Forecast | Brier |
| --- | --- |
| Published incumbent | 0.2095 |
| Incumbent-method replay | 0.2045 |
| Reduced challenger | 0.2007 |

- **Against the published incumbent:** the CI is [−0.021, −0.004].
- **Source of the gain:** about 60% comes from the replay without workbook priors, and the rest from the trend
  feature (CI against the replay: [−0.0043, −0.0006]).
- **Caveat:** this is a small sample from one season.

## M7: release

**Safeguards:** `.github/release-manifests/v8-protected-changes.json` is an additions-only manifest.
- **What it lists:** exactly the 21 V8 protected-path additions: `src/cfb_analytics/v8_*.py`, `research/v8/*` and
  `web/public/v8-team-stats.json`. Its pattern and modification sections are empty.
- **Scope:** it applies only to same-repository pull requests from `v8-development`.
- **Guard result:** `scripts/verify_protected_changes.py origin/main v8-development true -- <protected paths>`
  approves 21 additions and rejects nothing. Any other branch rejects them.
- **Guard test:** `tests/test_protected_guard.py` now asserts that this is the only manifest, that it is
  additions-only, that every other branch and forks stay strict, and that its list equals the V8 protected files in
  the tree (no unlisted additions).
- **After merge:** remove the manifest and restore the "no release manifest remains" test, as was done for V7 in
  PR #41.

**Freshness:** `v8-stats-refresh.yml` is dormant until it reaches `main`. It runs Sunday to Tuesday in season,
re-downloading games, drives and the latest two weeks of plays (about 7 calls). It commits the derived files only,
and the next routine dashboard deployment publishes them.

**Rollback:** revert the V8 merge commit. V8 adds files and a section without changing existing calculations, so
a revert restores the previous app exactly.
