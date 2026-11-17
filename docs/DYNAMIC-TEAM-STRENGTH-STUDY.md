# Dynamic team strength: recency-weighting study

**Decision: keep the incumbent prediction engine.** No tiered or other recency weighting showed a
meaningful predictive improvement without regression, so ratings, spreads, win probabilities and
playoff projections are unchanged.

Reproduce with `python scripts/dynamic_strength_backtest.py --output docs/evidence/dynamic-strength/study.json`
(about 20 s, no network). Tests: `tests/test_dynamic_strength_backtest.py`.

## 1. How the incumbent engine works

These are findings from reading `ratings.py`, `model.py`, `pipeline.py` and `backtest.py`:

| Question | Answer |
| --- | --- |
| How games affect ratings | Every completed game has **equal weight**. Each contributes the opponent's rating plus the margin (home edge removed, capped at ±45). There are 8 iterative passes, with a ridge pull toward the preseason prior (about 5 games' worth) and a conference-level shift |
| Recency | **None.** Week 2 counts as much as last week |
| Opponent strength | Built in through the iterative passes. FCS opponents are fixed at −26 |
| Offense and defense | **Not modelled separately.** There is one margin-based rating per team, and score-level offense/defense data isn't in the pipeline |
| Projected scores | **Not produced.** The model outputs a projected margin (spread = rating difference + 3 at home) and a win probability (logistic, scale 18). It produces no totals, so none were invented |
| Personnel changes | **Not modelled.** There are no quarterback, injury or coaching inputs; changes show up only through results |

## 2. Method

**Leakage-free walk-forward backtest:**
- Each week is predicted only from games completed before it, with same-week games sharing one
  snapshot.
- The engine is the incumbent's, with a per-(team, game) weight that depends on how recent the game is
  for that team.
- Weights are normalized per team to a mean of 1, so the prior's influence is unchanged.
- With all weights equal to 1, it reproduces `calculate_ratings` exactly. This is asserted on every
  run.

**Data:**
- **2016–2025:** the verified results archive (`espn-games.json.gz`), regular season plus
  postseason. Postseason games are ordered after the regular season.
- **Prior:** each team's previous-season final incumbent rating × 0.8. The 0.8 was chosen on training
  log loss, from 0.4–1.0, using the incumbent only, and is known before kickoff. There is no verified
  historical conference map, so one pseudo-conference was used, the same for every method.
- **2026:** the production roster, conferences and preseason priors with `data/cfbd-2026-games.json`.

**Split:**
- Every method was tuned on **2017–2019 and 2021**.
- The best tiered setting was then **pre-registered** and evaluated on held-out **2022–2025** and on
  **2026**.
- 2020 is excluded, as in the project's other research.
- Paired differences use 95% bootstrap intervals that resample whole weeks.

**Methods compared:**

| Method | Settings tried |
| --- | --- |
| Incumbent | Equal weights |
| Tiered (owner requirement) | The latest 3 games share one equal weight; the next 3 or 4 games share a second weight; older games weight 1. Recent weights 1–4 and middle weights 1–2: 37 settings. Tiers roll forward each game. A team with 3 or fewer games has all games equally weighted, which is identical to the incumbent. Bye weeks don't matter because tiers count games, not calendar weeks |
| Exponential decay | Half-life of 2–12 games |
| Window | The latest 4, 6 or 8 games at full weight, older games at 0.15 |
| Current-form term | k × (the team's mean residual over its last 3 games − the opponent's), added to the incumbent margin. Residuals are actual minus the incumbent's own pregame margin, so they are opponent-adjusted and don't double-count the rating. The 3 games are weighted equally |

## 3. Results

### Training (2017–2019, 2021; 3,180 games)

- The best tiered setting weights the latest 3 games ×1.5, the next 4 games ×1.25 and older games ×1.
- Its log loss is 0.4977 against the incumbent's 0.4980. Mild recency ranks best; strong recency
  (×2 to ×4) does not.

### Held-out 2022–2025 (3,275 games)

| Method | Brier | Change vs incumbent (95% CI) | Margin MAE | Accuracy | Calibration error |
| --- | --- | --- | --- | --- | --- |
| Incumbent | 0.1757 | — | 12.76 | 72.98% | 0.024 |
| Tiered, pre-registered (3 at ×1.5, 4 at ×1.25) | 0.1754 | −0.0004 (−0.0009 to +0.0001) | 12.75 | 72.73% | 0.024 |
| Tiered (3 at ×1.5, middle ×1) | 0.1754 | −0.0003 (−0.0010 to +0.0003) | 12.75 | 72.82% | 0.025 |
| Tiered, strong (3 at ×3, 3 at ×2) | 0.1755 | −0.0003 (−0.0016 to +0.0010) | 12.76 | 72.70% | 0.026 |
| Exponential, half-life 4 | 0.1754 | −0.0003 (−0.0017 to +0.0011) | 12.77 | 72.76% | 0.023 |
| Window of 6 | 0.1763 | +0.0006 (−0.0012 to +0.0025) | 12.81 | 72.67% | 0.025 |
| Form term, k = 0.05 | 0.1750 | **−0.0007 (−0.0012 to −0.0002)** | 12.73 | 72.98% | 0.020 |

### 2026 to date (653 games, production priors)

| Method | Brier | Change vs incumbent (95% CI) | Margin MAE | Accuracy | Calibration error |
| --- | --- | --- | --- | --- | --- |
| Incumbent | 0.1752 | — | 12.84 | 73.20% | 0.035 |
| Tiered, pre-registered | 0.1753 | +0.0001 (−0.0005 to +0.0006) | 12.84 | 73.35% | 0.029 |
| Form term, k = 0.05 | 0.1752 | +0.0001 (−0.0009 to +0.0010) | 12.82 | 73.35% | **0.044** |

**Momentum check** (10,000 team-games):
- Teams that beat the incumbent's forecasts by more than 7 points per game over their last 3 games beat
  the next forecast by 1.3 points on average.
- Teams that fell short by more than 7 missed the next one by 1.8 points.
- The slope is 0.12.

So recent form carries a small, real signal. But single-game noise is about 13 points, so the signal
moves probabilities very little.

**Interpretation:**
- **Tiered weighting:** it lowers the held-out Brier by 0.0004 at best, with an interval that
  includes zero. It is no better on 2026.
- **Form term:** it is the only variant with a statistically detectable held-out gain, but that gain
  is about 0.4% of the Brier score. It doesn't carry over to 2026, where calibration error worsens
  from 0.035 to 0.044.
- **Verdict:** neither meets the bar of meaningful improvement without regression.

## 4. Texas Tech quarterback case study

**Transition (reported).** According to news reports:
- Thomas "Tommy" Castellanos's eligibility was contested in court; he missed the Colorado game after
  an October 2 appellate ruling, and a later injunction restored it.
- Will Hammond started earlier games.
- Castellanos replaced Hammond for the October 31 Arizona game (a 34–26 win) and remained the starter.

**Sources:**
- [Yahoo Sports](https://sports.yahoo.com/articles/texas-tech-benches-hammond-turns-152114718.html)
- [Fox Sports](https://www.foxsports.com/articles/cfb/tommy-castellanos-starts-at-qb-over-will-hammond-with-no-13-texas-tech-coming-off-1st-loss)
- [CBS Sports](https://www.cbssports.com/college-football/news/thomas-castellanos-texas-tech-eligibile-ncaa-injunction/)
- [Heavy](https://heavy.com/sports/college-football/texas-tech-red-raiders/texas-tech-thomas-castellanos-ineligible-2-weeks-ago-future-doubt/)

The sources differ on some dates.

**The model against Texas Tech's 2026 results** (pregame incumbent margin, Texas Tech's perspective):

| Week | Opponent | Predicted | Actual | Residual |
| --- | --- | --- | --- | --- |
| 2 | at Oregon State | +22.3 | +11 | −11.3 |
| 3 | Houston | +8.3 | +2 | −6.3 |
| 4 | Sam Houston State | +26.0 | +35 | +9.0 |
| 5 | at Colorado | +13.0 | +22 | +9.0 |
| 7 | Arizona State | +16.5 | +28 | +11.5 |
| 8 | at Cincinnati | +11.4 | −13 | −24.4 |
| 9 | Arizona (Castellanos' first start) | +5.1 | +8 | +2.9 |
| 10 | West Virginia | +16.2 | +5 | −11.2 |
| 11 | at Oklahoma State | +3.2 | +25 | +21.8 |

**Finding.** Across the season, residuals average about 0. Under Castellanos they are +2.9, −11.2
and +21.8 (mean +4.5). Three games with that spread cannot separate a quarterback effect from normal
game noise. There is no evidence that the model systematically underrated Texas Tech after the
change. Texas Tech is currently rated 17.95, #14.

## 5. Major team changes

- **Personnel data.** The pipeline has no verified historical source for quarterback starters,
  injuries or scheme changes, so a personnel-change subgroup couldn't be backtested. Adding a new
  provider would be outside this assignment's scope.
- **Arbitrary bonuses.** No point bonuses were added. Such bonuses would be unvalidated and could
  double-count what results already show.
- **Coverage today.** Sustained improvement or decline is captured by results through the ratings.
  The momentum check measures how much it carries forward: about 12% of a team's recent
  over- or under-performance.

## 6. What would change the decision

- **Form term.** The k = 0.05 current-form term is the strongest candidate. Re-evaluate it once the
  2026 season is complete.
- **Personnel data.** Revisit if verified starting-quarterback data becomes available. Promotion
  would require a meaningful held-out gain, no calibration regression on the current season, and the
  owner's explicit approval, under the existing challenger-promotion rule.
