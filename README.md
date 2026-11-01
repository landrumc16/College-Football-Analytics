# College Football Analytics

Mobile-first college football rankings, game predictions, conference outlooks, playoff forecasts, team schedules and hypothetical matchups.

**Live dashboard:** https://landrumc16.github.io/College-Football-Analytics/

**Release status:** Version 1.0 application and visual acceptance verified; formal `v1.0.0` tag pending. See [release gates](docs/V1-RELEASE-GATES.md). [Deployment run 41345784302](https://github.com/landrumc16/College-Football-Analytics/actions/runs/41345784302) passed the production build, report validation, mobile browser tests, Pages deployment and live-site smoke test.

## Current implementation

- Python model for 2026 FBS rankings, remaining-game win probabilities and season projections.
- 10,000-run CFP Monte Carlo forecasts, projected bracket, conference title matchups and conference standings/strength.
- Responsive React/Vite dashboard: Rankings, Game Predictions, Conferences, CFP Forecast, School Schedule, What If?
- Historical performance against expectations from archived pregame forecasts; winner accuracy and Brier Score are calculated for genuine completed-game forecasts only. Earlier 20-game accuracy claims were not verified as FBS-only pregame forecasts and must not be used as validated performance. Zero eligible games means **no accuracy percentage**.
- Separate retrospective weekly backtest against the preseason baseline, clearly distinguished from genuinely archived pregame forecasts. Optional AP and Coaches Poll comparison is displayed only when a verified poll snapshot is published; poll ingestion is not yet automated.
- Daily scheduled and manual CFBD data-refresh workflow; separate GitHub Pages build and deployment workflow.
- Published report includes data provenance and timestamps; UI distinguishes demo data from live data and warns on stale or invalid timestamps.
- Automated Python tests, frontend production build and report-shape deployment validation.

## Important limits

- Only the 2026 season is supported with the frozen 138-school baseline priors. Other seasons are intentionally rejected.
- CFP outcomes are a model approximation, not official committee selections. Conference-specific title-game tiebreakers and complete committee selection logic are not modeled.
- Historical accuracy is prospective: never backfill a pregame prediction from information observed after a game.
- The original [Google Sheet](https://docs.google.com/spreadsheets/d/1kpCF_5_BNQx43IywvwpUra5-o6kcdMZBHwed1pDVJ54/edit) remains the parity reference. The November 1 CI run found zero discrepancies above 0.001 in the metrics covered by the numerical audit; this does not imply every spreadsheet formula was independently audited. Do not modify or retire the sheet as part of this release.
- A committed code change does not imply a successful deployment; check GitHub Actions.
- Never commit API keys; the refresh workflow uses the `CFBD_API_KEY` Actions secret.

## Development and verification

```bash
python -m pip install -e '.[dev]'
pytest -q
cd web && npm install && npm run build
```

GitHub Actions: [Dashboard build/publish](https://github.com/landrumc16/College-Football-Analytics/actions/workflows/dashboard.yml) and [CFBD data refresh](https://github.com/landrumc16/College-Football-Analytics/actions/workflows/refresh-data.yml).

Version 1.0 application and visual release gates are documented in [release gates](docs/V1-RELEASE-GATES.md); formal tagging and final HEAD verification remain.

## Project handoff

See [November 1 closeout](docs/chat-handoffs/2026-11-01-college-football-analytics-closeout.md) for historical context. The original milestone plan was superseded by this README and the release-gates checklist.
