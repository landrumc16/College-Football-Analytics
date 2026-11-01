# College Football Analytics

> **Latest project handoff (2026-11-01):** [Chat closeout and next-session startup](docs/chat-handoffs/2026-11-01-college-football-analytics-closeout.md). Read this before continuing; the original baseline plan below is historical and does not reflect all implemented features.

A reproducible college-football ranking, prediction, and season-simulation platform. The [existing Google Sheet](https://docs.google.com/spreadsheets/d/1kpCF_5_BNQx43IywvwpUra5-o6kcdMZBHwed1pDVJ54/edit) remains the reference until parity testing succeeds.

## Target stack
- Python and pytest: ingestion, rating model, predictions, simulations, backtests
- PostgreSQL: canonical teams, games, model versions, prediction snapshots
- GitHub Actions: scheduled data updates, tests, freshness monitoring
- React/TypeScript: private web dashboard, designed for optional public launch

## Delivery milestones
1. **Model parity**: inventory spreadsheet formulas, named ranges, scripts and data; export baseline fixtures; implement Python equivalents; compare team ratings/ranks and probabilities with tolerances.
2. **Reliable ingestion**: CFBD API adapter, incremental game sync, credential management, validation, deduplication, retries, alerts and last-success timestamp.
3. **Full forecasting**: game probabilities, remaining schedule, conference odds, CFP projection, 10,000-season simulation and historical backtesting.
4. **Usable dashboard**: Top 25, all rankings, teams, conferences, predictions, odds, schedule, accuracy and pipeline status.
5. **Cutover**: parallel runs and discrepancy reconciliation, then Sheets as optional export.

## Engineering rules
- Never commit API keys; store CFBD_API_KEY in GitHub Actions secrets.
- Preserve the existing model before modifying methodology. Improvements require separate validation.
- Distinguish data freshness errors from calculation errors; never silently publish stale results as current.
- Ship substantial tested increments rather than tiny speculative changes.
- Do not modify or retire the existing spreadsheet until the replacement is verified.

## Baseline observations (2026-10-31)
The Top 25 sheet reports Week 7 and 510 completed games. Team and dashboard formulas are calculating. The Season Checklist references an Apps Script function named `weeklyUpdate` and the `CFBD_API_KEY` Script Property. The updater's execution history has not been inspected, so the root cause of the stale data is not yet confirmed.

## Immediate next work
Export a frozen fixture from Teams, Games, PreseasonPrior, Model Settings, Predictions and Rankings; inventory named ranges and Apps Script behavior; implement Python calculation parity with regression tests. Keep the initial scope on one complete end-to-end data-to-ranking slice.
