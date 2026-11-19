# College Football Analytics — Version 8.0 Roadmap
**Title:** Advanced Team Intelligence & Matchup Prediction Engine
**Status:** Owner-authorized development; NOT approved for production or merge.
**Development branch:** `v8-development` | **Production:** `main`
**Baseline:** branch from current main after PR #41; record exact baseline SHA in first implementation report.
**Owner intent:** Unique, trustworthy offense/defense profiles and measurably improved game predictions, with no feature duplication.

## North star
For every FBS program, explain how its offense and defense actually performed against the competition faced; for each upcoming matchup, predict how those units interact using only verified information available before kickoff. Make this comprehensible to everyday fans and reproducible for researchers.

## Nonnegotiable rules
- Follow `AGENTS.md`: simplicity, reuse, surgical changes, meaningful tests, substantial end-to-end passes.
- Preserve V7 Market page, existing team pages, navigation, search, favorites, CFP, PWA, PostHog consent/privacy, rankings, historical archive, and production forecasts.
- Existing prediction engine remains authoritative until owner explicitly approves challenger promotion after objective evaluation. Do not silently change published predictions.
- Never invent quarterback status, injuries, play-by-play, odds, opponent quality, forecasts, or historical pregame snapshots. Explicit N/A and coverage are preferable.
- Every historical feature must be computed **as of the forecast date**, excluding future games and postgame knowledge; validate by season and week.
- P4-only is a **competition filter**, not a universal strength rating. Define conference membership by season, games versus P4 opponents, independents/Notre Dame treatment, postseason and conference transitions; publish eligibility and denominator. Retain all-FBS national adjusted rankings.
- Compare teams on a common opponent baseline; distinguish raw, P4-only, and schedule-adjusted metrics. Do not double count strength-of-schedule corrections.
- No added betting recommendations; V7 Market calculator stays in its single existing location.
- No merges to `main` or model promotion without explicit owner approval.

## Product architecture
- One authoritative **Offense & Defense** stats destination, linked contextually from Team Profile, Rankings, and matchup pages. Do not duplicate full panels across destinations.
- All FBS team profiles offer offense/defense overview, P4-only view (eligible P4 teams), adjusted strength, recent trend, matchup-specific splits, methodology, data coverage, last-updated/as-of.
- Side-by-side opponent comparisons highlight where the matchup differs from raw season averages, with explanatory text grounded in computed features.
- Keep mobile-first primary summaries short; expandable detailed metrics and methodology in Research & Data.
- Rankings clearly distinguish **descriptive performance** from **predictive strength** and show rank, metric, sample size, uncertainty, and coverage.

## Milestones and definitive completion gates

### M1 — Baseline and source feasibility
Inventory existing code, archived team-game/play-by-play data, team identity mappings, historical opponent stats, model feature pipelines, snapshots and licensed data. Verify what is available for points/drive, yards/play, success rate, explosive plays, rushing/passing splits, QB participation, injury/status and schedules. Establish conference-by-season classification and pregame timestamps.
**Done:** committed source/coverage matrix by season and metric; precise definitions and missing-data policy; tested joins, temporal availability, redistribution/licensing checks; baseline SHA and no invented sources.

### M2 — New statistical foundation
Implement reproducible raw and P4-opponent-only offense/defense metrics, with season-aware classification. Normalize by plays/possessions where supported; avoid garbage-time assumptions if unavailable. Build iterative opponent-adjusted ratings with regularization/shrinkage, schedule connectivity safeguards, and documented home/away treatment. Use common opponent baseline, quantify uncertainty and small samples. Publish both adjusted all-FBS and filtered P4 rankings.
**Done:** reproducible historical and current outputs; fixture-based arithmetic, P4 membership/transitions, Notre Dame/independents, FCS/G6 exclusions for P4 filter, low sample, ties, missing data and no-future-leakage tests; manual spot checks; validated rankings with denominators and provenance.

### M3 — Complete Offense & Defense profile
Deliver the single canonical destination with team search, sortable offensive/defensive leaderboards, raw/P4-only/adjusted tabs, recent 3–4-game vs season trend, opponent context, readable definitions, confidence/coverage and N/A. Contextual links from existing team profiles, rankings and matchup pages; no duplicate stat pages.
**Done:** working real-data end-to-end experience, keyboard/accessibility and viewport checks at 375/390/430/768/1536, no overflow, meaningful empty states, preserved navigation and PWA.

### M4 — Matchup features and roster context
Create matchup feature set from adjusted offense versus adjusted defense, rush/pass splits, pace, pressure/protection and explosive plays **only where measured reliably**. Test whether recent form and opponent style diversity improve held-out results; do not assume. Integrate verified QB starter/rotation/availability and key roster changes only with historical pregame timestamp and coverage; if unavailable, mark N/A and do not infer. Explain directional factors and their limitations.
**Done:** documented feature definitions and as-of contracts; opponent-specific calculations; missing/changed-QB cases; feature ablations; no leakage or ungrounded narrative.

### M5 — Challenger forecast model
Train/calibrate challenger with strict chronological walk-forward validation and appropriate regularization; compare to incumbent on exactly matched games. Produce win probability and margin only where supported; quantify uncertainty and explain important matchup drivers. Keep incumbent untouched and live.
**Done:** deterministic pipeline and frozen pregame-feature snapshots or reproducible as-of replay clearly labeled; paired evaluation by season, conference, favorite, QB-change, early/late season; Brier, log loss, calibration, winner accuracy, margin MAE where applicable, bootstrap confidence intervals; no unsupported claimed gains.

### M6 — Independent validation and promotion decision
Audit leakage, data quality, confounding, small-sample uncertainty, outlier games, P4/G6 transitions, QB change availability, and feature contribution. Compare to incumbent and optional timestamped market baseline on identical games; market not an input to independent forecasts. Publish negative results honestly. Require consistent meaningful out-of-sample improvement (pre-register numeric gates before model tuning), not a cherry-picked Texas Tech–Baylor result.
**Done:** reproducible evaluation report, exact test SHA, limitations, promotion recommendation (promote / retain incumbent). **No automatic promotion.** If challenger fails, ship validated descriptive analytics without replacing forecasts.

### M7 — Integrated release acceptance
Complete production-style mobile and desktop journeys, all relevant CI, Python/frontend tests, live-data freshness, accessibility, privacy/security, PWA update/offline/recovery, source provenance, no navigation duplicates, and user-facing matchup explanations. Preserve V7 Market calculations and prior poll fixes.
**Done:** exact-SHA release candidate, screenshots/verified browser runs, source coverage, rollback plan, explicit owner review and approval before merge; verify Pages deployment only after approval and merge.

## Execution order
1. Inspect `AGENTS.md` and actual main, inventory existing assets, implement M1–M2 as a substantial pass.
2. Implement and validate the complete usable M3 stats profile.
3. Build M4–M5 challenger without altering incumbent; execute M6 held-out tests.
4. Complete M7 and request one consolidated owner approval. Do not invent new versions or reopen completed milestones.

## Definition of finished
An everyday fan can inspect any FBS team's trustworthy offensive/defensive profile, distinguish P4-only performance from nationally adjusted strength, understand how opponent quality changes interpretation, and see transparent matchup factors. All outputs have real source coverage, reproducible definitions, meaningful sample-size and missing-data disclosures. A challenger prediction model is independently validated and either explicitly approved for promotion or clearly retained as research; production remains stable, all tests pass, and release has owner approval.

## Stop rule
Complete V8.0 as one coherent product improvement; do not spin off V8.1/V9 or add unrelated features.
