# Critical original-workbook audit: market-assisted prediction leakage

Source: original connected Google Sheet `1kpCF_5_BNQx43IywvwpUra5-o6kcdMZBHwed1pDVJ54`, inspected 2026-11-01. Read-only inspection of Model Settings, Predictions, Accuracy, Teams and Games.

## Findings

1. `Predictions!F6` predicted home margin = home rating minus away rating plus home-field advantage (zero on neutral site).
2. `Predictions!N6` is the **independent model** probability: `1/(1+10^(-F6/Win_Scale))`.
3. `Predictions!H6` is the **displayed probability**: `IF(ISNUMBER(M6),1/(1+10^(M6/Market_Scale)),N6)`. This switches to closing-market spread in `M6` whenever present. `Predictions!O6` identifies the source as `Market line` or `Model`.
4. Consequently, displayed winner picks in `Predictions!G6` derive from H6 and can be **market-assisted**. Never label those as model-only results or compare them with market odds as independent forecasts.
5. `Accuracy!N6:O8` displays claimed ten-season results: original untuned formula 0.717, tuned model 0.717, betting closing line 0.732. These are workbook-reported summaries, **not independently reproduced**.
6. `Model Settings` says tuned on 2016–2021 and checked on 2022–2025; also describes a 2026 early-season holdout and roster-based prior improvement. Those claims require the underlying archived records and split definitions before being used as verified performance.
7. `Teams!F4` uses `Prior_Weight * VLOOKUP(... PreseasonPrior ...)`, while `Model Settings!B8` displays 1 and explanatory text says historical best 0.7. Resolve actual named range and formula provenance before changing model constants.
8. `Games!G4` removes home advantage and caps adjusted margin; `Teams!G4:S4` applies iterative opponent adjustment, conference shrink and ridge priors. Preserve workbook parity tests.

## Required benchmark split

- **Independent workbook model**: archive `Predictions!N` with as-of rating inputs and generated timestamps.
- **Market-assisted spreadsheet display**: archive `Predictions!H` and `O` separately; this is a blended/fallback product, not a market-independent model.
- **Market benchmark**: capture closing spread and/or de-vigged moneyline independently, with source and timestamps.
- **V2 model**: archive independent pregame probability and projected margin.

Score all three independently on the same verified FBS–FBS games; do not claim market parity from workbook H/G columns. If historical as-of forecasts cannot be established, report retrospective walk-forward results distinctly.
