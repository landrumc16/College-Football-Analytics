# V7 Milestone 3: market comparison and metrics engine, results

**Branch:** `v7-development` (draft PR #33, NOT FOR MERGE). **Scope:** `docs/V7-ROADMAP.md` M3.
Nothing was merged or deployed. V6 production, the public beta and PR #34 are untouched.
Kalshi remains blocked.

## 1. What was built

**`src/cfb_analytics/v7_market_metrics.py`** is a pure, offline engine. It needs no network, no
private data, no new dependency and no new model.

It reads only already-published, licensed inputs:
- `web/public/v7-team-lines/<team>.json`: M2's single named provider's closing spread and total per
  game;
- `data/pregame-2026-history.json`: the existing forecast ledger;
- `research/archive/verified/verified-pregame-rows.json`: the independently verified publication
  cohort.

It reuses the existing validated spread-to-probability conversion (`model.market_home_win_probability`,
scale 19.5) and M2's slug and licence constants.

It writes two outputs:
- **`web/public/v7-market-metrics.json`** (848 KB, compact): team aggregates, the national
  calibration and the model-vs-market summary. It contains no per-game lines, game IDs or providers.
- **`web/public/v7-model-market/<team>.json`** (137 files): per-game model-vs-market rows, each with
  one named provider. These are for team and game pages only. There is no combined file, index or
  download link.

Runs and checks:
- `python -m cfb_analytics.v7_market_metrics` builds; `--check` regenerates and requires
  byte-identical output.
- Writes are atomic: everything is staged, then swapped in.
- A rejected build writes nothing.

Workflows:
- The backfill workflow regenerates and `--check`s the metrics after every archive rebuild, runs the
  tests, and commits only the allow-listed outputs. The leak scan now covers the new files too.
- `refresh-data.yml` gains an isolated `continue-on-error` metrics step, effective only after a
  future merge.

## 2. Metrics implemented (per team: all seasons, plus current season)

| Metric | Definition | Safeguards |
| --- | --- | --- |
| ATS record and cover rate | W-L-P against the closing spread; rate = W/(W+L) | Pushes shown, excluded from the denominator; Wilson 95% interval; sample label; rate withheld below 10 decided games |
| Over/under record and over rate | O-U-P against the closing total | Same |
| Home / away / neutral splits | ATS and O/U by venue | Same |
| Favourite / underdog / pick'em splits | ATS, O/U and mean cover margin by closing-spread role | Same |
| Cover-margin distribution | Team margin + team closing spread: n, mean, median, SD, quartiles, 9 buckets (push separate) | N/A below 5 games |
| Total-margin distribution | Combined points − closing total | N/A below 5 games |
| Market-implied win probability | Closing spread → probability (logistic, scale 19.5) | Caveat published (§4); tied finals excluded |
| Wins vs market expectation | Actual wins − sum of implied win probabilities | Descriptive only; N/A below 10 games |
| Last 5/10/20 | ATS and O/U, most recent first | — |
| ATS including disputed games | Sensitivity alongside the primary figure | Primary figures always exclude disputed games |
| Exclusions | `no_line`, `disputed`, `suspicious`, `no_result` per market | Every excluded game is counted with its reason |

**National: calibration of the spread-implied probability.** 9,273 games (2016 to 2026 to date), each
counted once from the home side; non-disputed spreads; completed, non-tied games.

| Measure | Result |
| --- | --- |
| Brier score (all games) | 0.1586 |
| Brier score by season | 0.147–0.168 |
| Mean implied probability vs observed win rate | Within 0.04 in every bin with 300 or more games |

**National: multiple-comparisons disclosure.**
- 135 teams have an adequate ATS sample (30 or more decided games).
- 6 of them have a 95% interval that excludes 50%.
- 6.8 would be expected by chance alone.

The published note says an excluded interval is not proof of a lasting trend.

## 3. Model vs market (authentic pregame forecasts only)

**What qualifies.** A forecast is used only when all of the following hold:
- the ledger marks it `generated_before_kickoff` by an identified model;
- `forecast_recorded_at` is before both the scheduled kickoff and the archived kickoff (this
  protects against reschedules);
- its probability and margin are valid;
- it joins by game ID, with team names matching, to the selected provider's non-disputed closing
  spread.

When the home team is non-FBS, the line comes from the away team's file, inverted. When a game is in
the independently verified publication cohort, the record must agree exactly with the ledger, or the
build fails.

**What is compared.** The model's existing outputs:
- win probability, against the spread-implied probability (difference in probability points);
- projected margin, against the margin implied by the closing spread;
- favourite agreement;
- hours between the recorded forecast and kickoff.

| Population | Games | Mean / median absolute probability difference | Mean / median absolute margin difference | Favourite disagreement | Median hours before kickoff |
| --- | --- | --- | --- | --- | --- |
| All authentic (2026 Weeks 10–13) | 125 | 7.8 / 5.9 pts | 3.3 / 2.8 pts | 21 | 150.9 |
| Independently verified subset | 65 (all 65 retained) | 7.2 / 5.5 pts | 2.9 / 2.4 pts | 8 | 51.2 |

**Excluded, with reasons:**

| Reason | Forecasts |
| --- | --- |
| Neither team is a current FBS program, so no licensed line exists | 577 |
| Game not played yet, or no line in the archive | 136 |
| Carried-forward entry without a pre-kickoff generation record | 20 |

**Not produced:**
- **Totals:** `model_total` is `not_available` in both outputs, because the incumbent model does not
  produce game totals. The guards reject any other model-total output.
- **Retrospective replays:** `retrospective_replays.used` is false. No model forecasts were archived
  before kickoff for 2016–2025. Retrospective calculations, including the V6 research challenger
  replay, are not used and are not presented as pregame predictions. The historical model
  comparison is `not_available`.

**Caveats published with the data:**
- The closing line is observed after the forecast was recorded, so the two are not simultaneous.
- Differences describe disagreement only. They are not edges or picks.
- Accuracy comparison on identical games is left to M6.

## 4. Implied-probability methodology and caveat (published verbatim)

> Approximate win probability derived from the closing point spread with the existing logistic
> conversion (scale 19.5 points, fitted on 7,560 FBS games 2016-2025). Spreads are quoted at roughly
> equal prices on both sides; no moneyline prices or bookmaker margin (vig/fees) are used, so this is
> not a traded price, an executable quote or a share of bets or money.

## 5. Licensing and privacy

**Aggregate file (`assert_metrics_safe`).** The guard rejects:
- `spread`, `total`, `home_spread`, opening values, moneylines;
- providers, game IDs and `lines`;
- any model-total output.

**Comparison files (`assert_comparison_safe`).** The guard requires:
- the exact field set;
- `forecast_kind == authentic_pregame`;
- exactly one named provider;
- the forecast recorded before kickoff;
- no duplicate games;
- no extra keys, such as download links.

**Opening-line movement.** Not published, because the CFBD permission covers closing lines only.
The limitations list says so.

**Raw multi-provider data.** Never read. Inputs are M2's already-licensed public files.

## 6. Independent validation

1. **Cross-source recount.** M3 recounts ATS and O/U totals, venue and role splits from the public
   per-game files. These must equal M2's statistics, which are computed separately from private
   outcomes, **exactly for all 138 teams**; any difference fails the build. For example, Texas Tech
   is 73–57–5 ATS and 69–62–1 O/U in both.
2. **Plain-code recomputation over real data.** A separate loop recomputes, without the engine's
   helpers:
   - every team's mean cover margin, implied expected wins and actual wins;
   - every comparison row's probability and margin differences.

   All match.
3. **Hand-computed fixtures.** These cover:
   - wins, losses, pushes (spread and total), pick'em;
   - unplayed/void games, tied finals, missing lines, disputed and suspicious values;
   - bucket boundaries, quantiles, Wilson intervals (against published values), sample-label
     boundaries;
   - home/away/neutral and favourite/underdog classification, last-N ordering, calibration
     de-duplication;
   - all ten authentic-forecast rejection reasons, including reschedules and a `retrospective_replay`
     source;
   - inverted lookup through a non-FBS home team, team mismatch, verified-record conflict;
   - guard rejections, atomic write and `--check`.
4. **Mutation check.** Breaking the push rule, the favourite rule or the disputed exclusion each makes
   the tests fail.

## 7. Tests

| Suite | Result |
| --- | --- |
| `tests/test_v7_market_metrics.py` | 39 passed |
| Full `pytest` | 667 passed: 628 existing (unchanged) + 39 new |
| Frontend `npm run build` and `scripts/verify_dashboard_bundle.py` | Pass. No app source changed in M3 |
| Leak scan (278 public files) | Pass |

CI results for the pushed commit are recorded in the closeout report.

## 8. Coverage and limitations

- **Team metrics.** 2016–2025, plus 2026 completed games, for the 138 current FBS programs.
  - Overall ATS sample: 135 teams adequate, 3 limited.
  - The current season is necessarily limited: 114 teams limited, 24 insufficient.
- **Model vs market.** Only the 2026 forecasts recorded before kickoff, on completed games that have
  a licensed line: 125 games, of which 65 were independently verified. Upcoming games have no
  closing line in the archive yet; current lines belong to M4.
- **Not implemented, with reasons:**

  | Item | Reason |
  | --- | --- |
  | Opening-to-closing movement | Not licensed |
  | Model totals | Not produced by the model |
  | Historical model comparison | No authentic archive |
  | Accuracy comparison | M6 |
  | Opponent-strength context | Not in the M3 done criteria |
  | Prediction-market probabilities | Kalshi blocked |

## 9. Acceptance criteria

| # | Criterion | Status |
| --- | --- | --- |
| 1 | Every approved comparison metric implemented | ✅ §2, §3 |
| 2 | Calculations independently validated | ✅ §6 |
| 3 | Historical and authentic pregame predictions clearly distinguished | ✅ Authentic only, with tiers labelled; retrospective explicitly unused |
| 4 | No unsupported model outputs or predictive claims | ✅ No model totals (guarded); differences labelled non-predictive |
| 5 | Missing data and uncertainty handled correctly | ✅ Reasons, N/A thresholds, Wilson intervals, multiple-comparisons note |
| 6 | Existing functionality and licensing protections intact | ✅ No V6 or app change; M2 guards unchanged; new guards added |
| 7 | Required tests pass | ✅ §7 (CI in the closeout report) |
| 8 | Implementation and evidence committed to `v7-development` | ✅ |

## 10. Next

M4 (Market Watch) was withdrawn by the 2026-11-16 market analysis refocus. The remaining market-comparison
feature is the user-powered Market Analysis Calculator: see the amendment in `docs/V7-ROADMAP.md` and
`docs/V7-MARKET-CALCULATOR.md`.
