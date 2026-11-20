# "Why this prediction?" explanations

**Where it appears:** every Game Predictions card has a "Why this prediction?" expander, which is the existing "Why
this pick?" expander now showing more. There is no new page and no new model.

**Files:**

| File | Role |
| --- | --- |
| `src/cfb_analytics/explain_publish.py` | Writes the data file (`python -m cfb_analytics.explain_publish`) |
| `web/public/prediction-explanations.json` | The data file |
| `web/src/predictionExplanations.ts` | Plain-English wording, built only from the published numbers |
| `web/src/WhyThisPrediction.tsx` | The card's expander |
| `web/src/prediction-explanations.css` | Styles |

## Where the numbers come from

Every point value is an exact part of a published forecast, so the parts always add up to that forecast's margin. The
tests check this for every game.

### Official forecast

The official engine (`ratings.calculate_ratings`) is re-run from the same frozen roster and CFBD snapshot as the season
report. Publishing stops unless every rating and margin equals the report.

A rating is (sum of game values + 5 × preseason prior) / (games + 5), where a game value is the opponent's rating plus
the home-adjusted margin. The margin therefore splits into three parts:
- this season's games;
- the preseason carry-over, including the existing conference adjustment;
- home field (3.0 points, or 0 at a neutral site).

### Standard and Momentum

These are re-run exactly as `dual_publish` does, and a test checks that their margins equal `dual_publish.build` for
the same inputs. Each one splits into:
- **Season games, carry-over and home field:** from net rating = (weighted game values + 3 × prior) / (weights + 3).
  Home field is fitted, about 3.3 points.
- **Offense vs. defense:** projected points = league average + offense + opponent defense + home field.
- **Momentum's shift:** Momentum minus Standard.

### Context, not points

These facts are shown but never added as separate points:
- schedule strength and quality wins (from the official engine);
- records;
- last-three-game form;
- each team's weakest game.

Schedule strength is already inside the ratings, and the page says so.

## Safeguards

- **No new model:** no prediction formula, rating or published probability changes. If a decomposition does not close,
  publishing raises an error.
- **Matching the card:** an explanation is shown only when its official margin equals the margin on the card. The two
  files refresh together during deployment. If they differ, or the file is missing, the card keeps its published
  one-line summary and says the explanation is being refreshed.
- **Not inferred:** quarterback changes (no verified pregame source), injuries, weather and travel are listed as "Not
  included in any model".
- **Notes:** these are written only from facts in the data. One example: a win over an FCS team counts as a team's
  weakest game, because all FCS opponents are treated as one average FCS team (see the Texas Tech at Baylor audit).

## Deployment

The dashboard build:
1. regenerates the file from the final rebuilt season report (after the V6 packets step);
2. copies it into the site.

A failure keeps the committed file and never blocks deployment.

## Tests

| Test | What it checks |
| --- | --- |
| `tests/test_explain_publish.py` | The official parts rebuild every published margin; the dual margins equal `dual_publish`; the Texas Tech at Baylor audit values; tampering stops publishing |
| `web/tests/prediction-explanations-unit.mjs` | The wording: exact sums, the audit case, variety across games, no filler |
| `web/tests/prediction-explanations.mjs` | Browser checks at 375, 390, 430, 768 and 1536px plus Android Pixel 7 emulation: keyboard use, contrast, overflow, the missing and stale fallbacks, and the existing card buttons |
