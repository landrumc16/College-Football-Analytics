# V7 Market Analysis Calculator: results

**Branch:** `v7-development` (draft PR #33, NOT FOR MERGE). **Scope:** the owner's 2026-11-16 market
analysis refocus, recorded as an amendment in `docs/V7-ROADMAP.md`.

Nothing was merged or deployed. V6 production, the public beta and PR #34 are untouched. There are
no live feeds and no Kalshi or other third-party market retrieval.

## 1. What users get

The calculator sits in **Teams → Compare & What If**, below the model's projected winner, once two
FBS schools and a location are chosen.

**Choosing a side.** The user picks which team's perspective to compare from, using a labelled radio
group that also works with the arrow keys.

**Three inputs.** Each is optional and calculated independently:

| Input | User enters | Compared with | Difference |
| --- | --- | --- | --- |
| Point spread | The selected team's line (−7 = favoured by 7; `PK` or 0 = pick'em) | Model projected margin for that team | Model margin + entered spread, in points (positive = model more favourable to the team) |
| Prediction-market probability | 0–100% for the selected team | Model win probability for that team | Percentage points |
| American moneyline | ≤ −100 or ≥ +100 | Model win probability | Percentage points against the **raw** implied probability: 100/(odds+100) for positive odds, \|odds\|/(\|odds\|+100) for negative |

**What each result shows:**
- the model's number;
- the number the user entered;
- the signed difference;
- a plain-English sentence;
- the label: *"Market number entered by you; not retrieved or verified by this app."*

**Disclosures on the page:**
- The moneyline help text says the bookmaker's margin (vig) is **not removed**, so the figure
  usually overstates each side's chance.
- A closing note says a difference is not a forecast of profit or a recommendation to wager.

## 2. Model source: actual outputs only

1. **Published pregame forecast.** When the chosen schools and location match a scheduled game in
   the current report, its published `home_win_probability` and `home_margin` are used. These are the
   same values shown on the prediction cards. The calculator labels this "Published forecast" with
   the game's week.
2. **Hypothetical matchup.** Otherwise the calculator uses the matchup calculation the Compare page
   already shows: the same incumbent model, the current published ratings and the home-field
   adjustment. It is labelled "Hypothetical matchup" and states that it is not a published game
   forecast.
3. **Missing output.** If the model output is missing or invalid, the calculator says "Model
   prediction unavailable" and shows no inputs. It never estimates a value.

Retrospective replays and archived research calculations are not used.

## 3. Perspective, signs and edge cases

**Switching team** (`teamView`) flips the model margin and probability (*p* → 1 − *p*). It also
re-expresses the same entered market:
- the spread is negated (−6.5 becomes +6.5);
- the probability becomes 100 − *p*;
- the moneyline is cleared, with an explanation, because the other side's odds cannot be derived when
  bookmaker margins differ by side.

**Edge cases:**
- **Pick'em:** `PK`, `pick'em`, `even` and 0 are accepted.
- **Signs:** −0 is normalised, and no "−0.0" is ever shown.
- **Characters:** typographic minus signs and stray spaces are accepted.

**Rejected input.** Each rejection shows an inline message and sets `aria-invalid`:
- spreads beyond ±99.5;
- probabilities below 0 or above 100, or with a sign;
- moneylines between −100 and +100, or beyond ±100000;
- non-numbers, `1e3`, `Infinity` and `NaN`.

## 4. Privacy

Entered values exist only in React component state. They are never placed in:
- analytics (`analytics.ts` sends only explicit page events, and the calculator calls none);
- `localStorage` or `sessionStorage`;
- the URL;
- any request.

State resets whenever the matchup or location changes. The browser test asserts at every width that
no entered value appears in any request URL query, request body, stored value or the page URL.

## 5. Implementation (small and local)

| File | Change |
| --- | --- |
| `web/src/marketCalculator.ts` | Pure functions: parsing, conversion, perspective, differences, explanations |
| `web/src/MarketCalculator.tsx` | Accessible component: labelled inputs, `aria-describedby`, polite live regions, 44px targets, focus outline |
| `web/src/main.tsx` | Chooses the model source (§2) and renders the calculator under the matchup result; adds the optional `neutral_site` field to the `Prediction` type |
| `web/src/style.css` | Mobile-first styles: one column below 900px, three columns above |

No dependency, data file, Python model or licensing guard changed. M2's private store and CFBD
safeguards are untouched.

## 6. Tests

**`web/tests/market-calculator-unit.mjs`** has 10 groups of hand-computed fixtures:
- moneyline conversion: −150 → 60%, +130 → 43.48%, ±100 → 50%, two sides at −110 summing to
  104.8% (vig retained), extremes and rejections;
- parsing boundaries for all three inputs;
- perspective reversal;
- spread sign cases (favourite, underdog, pick'em, symmetry);
- probability differences;
- no negative zero;
- exact explanation text, with a check for betting language;
- re-expression on team switch.

**`web/tests/market-calculator.mjs`** runs in Chromium at 375, 390, 430, 768 and 1536px:
- the published source and week label for a real scheduled FBS game;
- all three comparisons against independently computed values;
- three "entered by you" labels, the vig and no-wager disclosures;
- a keyboard team switch (+6.5, 58.7, moneyline cleared, differences reversed);
- invalid moneyline and probability messages with `aria-invalid`;
- pick'em;
- 44px inputs and no horizontal overflow;
- no entered value in requests, storage or the URL;
- a venue change giving the hypothetical source with entries reset;
- a missing model probability giving the unavailable message with no inputs.

Both tests run in the existing `frontend` CI job (`.github/workflows/v5-acceptance.yml`).

**Local results** on this change:

| Check | Result |
| --- | --- |
| New unit test | PASS (10 groups) |
| New browser test | PASS (5 widths and the missing-model case) |
| `mobile-smoke` (five widths and the Android Chrome-emulated PWA install/update/offline/recovery) | PASS |
| `editorial-home`, `v6-browser`, `v6-scenarios`, `historical-publication` | PASS |
| Production build and `verify_dashboard_bundle.py` | PASS |
| Full `pytest` | PASS |

Screenshots: `docs/evidence/v7-market-calculator/calculator-390.png` (2×) and `calculator-1536.png`.

## 7. Limits

- The spread comparison uses the model's projected margin, a published model output. The model
  produces no totals, so there is no totals input.
- Differences are descriptive. Whether model–market disagreement carries information is a
  Milestone 6 validation question, and no such claim is made here.
