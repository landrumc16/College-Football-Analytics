# V2 historical evaluation — input contract and first-run checklist

The V2 evaluator consumes two JSON arrays and **does not manufacture retrospective pregame forecasts**.

## Inputs

`games.json`: one row per historical game with `schema_version` (default 1), `season`, `game_id`, `home`, `away`, `home_division`, `away_division`, `kickoff`, `source_retrieved_at`, `source`, and completed `home_score`/`away_score` (or both null). Division values: `FBS`, `FCS`, `OTHER`, `UNKNOWN`. The roster must be season-specific. Times must be offset-aware ISO 8601.

`forecasts.json`: one row per archived forecast with `season`, `game_id`, `home_win_probability`, and `generated_at` (offset-aware ISO 8601). Forecasts must include `input_retrieved_at` (timezone-aware), the timestamp of the **forecast input snapshot**. The input snapshot must be retrieved no later than forecast generation, and generation must precede kickoff. The completed-game `source_retrieved_at` may be postgame and is not used to establish forecast validity. Missing or unverified forecast input timestamps are excluded rather than reconstructed.

Run:

```sh
python -m cfb_analytics.historical_cli --games games.json --forecasts forecasts.json --output v2-scorecard.json
```

Output: overall winner accuracy, Brier score, log loss, season-level metrics, total scored and exclusion counts. An empty valid sample has null metrics rather than invented accuracy.

## Required before reporting real performance

1. Obtain licensed/authorized multi-season CFBD game records, kickoff timestamps, retrieved-at provenance, and season-specific FBS/FCS membership.
2. Identify genuine archived pregame predictions with their generation times. Do **not** derive them from end-of-season ratings.
3. Run the CLI and preserve the exact input snapshots and output alongside source/version metadata.
4. Compare matching games and periods against the frozen V1 weekly backtest, while labeling its retrospective weekly predictions separately from genuinely archived prospective forecasts.
5. Add chronological walk-forward **model generation** only after establishing season-specific historical priors; this CLI is a scorer, not a model-training or forecasting engine.

CI runs tests, but it cannot establish real historical accuracy without genuine data.
