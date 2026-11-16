# College Football Analytics — Version 7.0 Authoritative Roadmap
**Working title:** Market Intelligence  
**Status:** Owner-approved product direction; roadmap proposed for review. No V7 implementation, deployment, or production change authorized by this document.  
**Repository:** `landrumc16/College-Football-Analytics`  
**Baseline:** released V6 plus PR #31 consent/analytics; use the actual current `main` SHA at implementation start.  
**Planning branch:** `v7-market-intelligence-roadmap`  
**Target:** optional educational market-analysis destination, not a sportsbook, picks service, or trading interface.

## North star
Help college football fans understand how independent football analysis, historical team performance, sportsbooks and prediction markets relate. Explain disagreements, data quality and uncertainty without telling people what to wager or trade. Preserve the existing fan-first homepage and all released V5/V6 capabilities.

## Non-negotiable product boundaries
1. Market Intelligence is a separate, optional destination; not the default homepage. Keep rankings, predictions, team profiles, program intelligence, comparisons, playoff tools, favorites, research, PostHog consent and mobile PWA intact.
2. Informational analytics only. No picks, recommended stakes, "locks", bet slips, broker/exchange accounts, trade execution, push-to-bet notifications, automated trading or promises of profit.
3. No fabricated spreads, totals, prices, market volume, order flow, model estimates or historical pregame predictions. Show N/A and explain gaps.
4. A market probability, traded price, executable quote, spread, total and a share of trading volume are **different measures**. Never infer that 80% probability means 80% of people or money backed one side.
5. Market disagreement is not an actionable edge. Flags describe observable divergence, liquidity, freshness or movement; calibrate thresholds against historical evidence and show uncertainty and counter-explanations.
6. Use verified as-of timestamps, event/contract rules, team normalization, data licenses and settlement rules. Never use postgame information in pregame validation.
7. Prefer existing Python/TypeScript, scheduled data pipeline, static publishing and testing. Do not introduce a persistent server unless a verified requirement cannot be met otherwise.
8. Preserve V6 production during the beta. Research and roadmap may proceed; implementation/release only on explicit subsequent owner instruction. No merge to `main` without explicit owner approval.

## Amendment — market analysis refocus (owner decision, 2026-11-16)

The owner approved a simplified, **user-powered Market Analysis Calculator** as the core remaining V7
market-comparison feature.

**Unchanged.** M1–M3 are complete and kept (`docs/V7-M2-RESULTS.md`, `docs/V7-M3-RESULTS.md`).

**Withdrawn.** These will not be built:
- live odds feeds;
- automated prediction-market integrations, including any Kalshi retrieval or publishing;
- continuous market monitoring;
- liquidity or stale-market alerts;
- line-movement tracking.

**Market Watch replaced.** The *Market Watch* section and M4 below are replaced by the calculator,
which is integrated into the existing Compare & What If matchup view. The user types:
- a point spread;
- a prediction-market win probability;
- an American moneyline.

The calculator compares each with the model's actual output for that matchup and that team. The
entered numbers stay in the browser: they are not retrieved, verified, stored or transmitted. M5 is
narrowed to this integration.

**Still applies.** M6 (honest historical validation on archived closing lines) and M7 (release
verification) are unchanged, as are all boundaries above.

Results: `docs/V7-MARKET-CALCULATOR.md`.

**Information architecture (owner decision, 2026-11-16): one feature, one home, links instead of duplication.**
- The bottom navigation is Home | Rankings | Teams | Playoffs | **Market**.
- Research & Data remains a full destination, opened from the top menu.
- The Market Analysis page is the calculator's only location. Compare & What If and the homepage
  link to it rather than embedding it.

See `docs/V7-RELEASE-ACCEPTANCE.md`.

## User-facing product
### Market Intelligence landing
Mobile-first overview of upcoming games with available model/market comparisons, timestamp and source, expandable explanations and clear unavailable states. Sections: **This Week**, **Market Watch**, **Team Market History**, **Learn & Research**. No intrusive wagering language or bet-oriented homepage takeover.

### Game detail
- Existing verified model win probability and explanation; market-implied probability with quote type, bid/ask/last distinction, fees caveat, observation time and contract resolution terms.
- Model projected margin and total **only if** already produced by a verified model or separately validated under explicit approval. Do not back-solve or invent.
- Compare like-for-like outcomes (regulation versus overtime, winner versus spread, market closing rules, postponement/void conditions).
- Display absolute probability-point difference, model uncertainty, liquidity and age of quote; no "value bet" badge.
- Historical comparable games only when sufficient samples and legitimate as-of data exist.

### Team Market History
ATS overall and by season; favorite/underdog; home/away; last 5/10/20 and season filters; over/under record; cover margin; opening/closing movement; opponent-strength context. Show pushes, no-action/void rules, exact source, denominator and coverage. Descriptive records are not future-win probabilities.

### Market Watch (withdrawn 2026-11-16, see Amendment)
Kalshi-first feasibility, with sportsbook closing lines for ATS/totals if lawful and licensed. Prices, bid-ask spread, volume, open interest, liquidity and historical movements where available. Distinguish current order book from historical trade/candle data; never claim historical order-book depth unless snapshots were actually retained. Flags: model disagreement, stale/thin/wide market, unusual price movement. No claims about trader identities, sentiment, money percentages or causation without direct evidence.

### Education and research
Plain-language tooltips for spread, ATS, push, totals, implied probability, bid/ask, liquidity, fees, market rules, sample size, regression to mean, model calibration and uncertainty. Accessible methodology, sources, limitations and historical validation separate from concise everyday UI.

## Data contracts and source feasibility
- Inventory existing archived football games, model snapshots and team identity mapping first; reuse verified assets.
- For each sportsbook line: provider, license, market/game/team identifiers, line type, open/close definition, timestamp, odds/price, result/void status, collection method, quality flag and permitted redistribution.
- For each prediction market: provider, event/contract ID, outcome semantics, open/close/settlement rules, observation time, bid, ask, last trade, trade volume, open interest, market status, source and freshness.
- Keep raw source snapshots immutable when permitted; store normalized, versioned derived data with provenance, retrieval receipts, checksums and coverage reports.
- Evaluate Kalshi public market/history/candlestick/trade interfaces and terms directly against current official documentation; availability of endpoints is **not** a license to republish data. Current depth may need credentials; historical depth cannot be inferred from candles. Determine realistic polling cadence, rate limits, hosting costs and freshness before choosing architecture.
- Independently evaluate licensed historical sportsbook closing lines. If no lawful reliable source exists, do not publish invented ATS/totals history; ship only verified subsections or report a release blocker.
- Keep public artifact small; do not publish restricted raw corpora, credentials or personal trading data.
- Schedule updates with retry/backoff, last-good snapshot, stale banner, failure alert and reproducible recovery. Do not present stale observations as live.

## Milestones and acceptance gates
### M1 — Feasibility and verified source plan
Inspect repository baseline, current archive, current model outputs, GitHub Pages deployment and data constraints. Verify Kalshi official API/terms, historical market coverage, sportsbook historical ATS/total licensing and availability, costs and sample completeness. Decide smallest supported end-to-end slice and document genuine gaps.
**Done:** source matrix (fields, temporal coverage, license, costs, cadence, rate limits), sample retrieved and verified from each selected source, explicit go/no-go for each feature, architecture decision, preserved baseline SHA. No implementation claims based on documentation alone.

### M2 — Historical market archive
Ingest licensed spreads/totals and permitted prediction-market historical observations; normalize game IDs, outcomes, time zones, pushes/voids and contract resolution. Record source and as-of times. Reuse existing historical archive.
**Done:** reproducible dataset and schema, coverage by season/team/provider, freshness and provenance reports, integrity tests (duplicates, bad joins, impossible prices, future leakage, inconsistent results), and verified sample hand-checks. Missing history explicitly N/A.

### M3 — Comparison and metrics engine
Calculate ATS, totals, cover margins, home/away/favorite/underdog splits, implied probabilities with quote/fee caveats, model-market differences and appropriate uncertainty. Only use model outputs actually supported.
**Done:** independent calculation fixtures, pushes/voids/price boundary tests, cross-source contract comparability tests, no unsupported model-margin/total outputs, sample-size labeling and explainable N/A states.

### M4 — Market Watch and cautious flags (withdrawn 2026-11-16; replaced by the Market Analysis Calculator, see Amendment)
Ingest available current market observations, store permitted historical snapshots, chart observed movement, flag stale/wide/thin markets and evidence-supported model-market differences. Never equate probabilities with share of trades.
**Done:** real-source end-to-end demonstration, clear timestamps and source, historical-vs-live distinction, threshold documentation and sensitivity tests, simulated stale/429/outage/recovery tests, no trade execution or calls to action.

### M5 — Integrated mobile-first UI (narrowed 2026-11-16 to the calculator in Compare & What If, see Amendment)
Build optional Market Intelligence destination with This Week, Market Watch, Team Market History and Learn & Research; contextual links from existing game/team pages only where helpful. Keep default homepage and current navigation concise.
**Done:** real-data journeys at 375/390/430/768/1536px, accessible keyboard/focus/contrast/touch/text enlargement, meaningful empty and stale states, no horizontal overflow, no changes to incumbent predictions, rankings, CFP, favorites or PWA.

### M6 — Honest historical validation
Compare model and market forecasts on identical pregame observations and game samples; separate authentic archived predictions from retrospective replays. Evaluate Brier/log loss/calibration, season/segment stability and uncertainty intervals; test whether disagreement provides information beyond market alone, accounting for fees and executable quotes if claims require them.
**Done:** frozen reproducible held-out evaluation with timestamps, baselines, coverage, confidence intervals and limitations; no hindsight or profitability claims without defensible evidence. If evidence is weak, publish the negative/inconclusive finding.

### M7 — Release verification and closeout
Run targeted and full Python/frontend tests, static build, privacy/security checks, production-data checks, browser/PWA regression, accessibility and human usability where available; validate production update failure recovery and PostHog consent/test separation. Confirm licensing and no new private data exposure.
**Done:** all required CI green on exact SHA; documented source licensing and freshness; real deployment smoke, screenshot/viewport evidence, owner-reviewed release candidate; explicit owner approval before merge; verified GitHub Pages production and closeout receipt. Distinguish physical devices from emulation.

## Definition of finished
A fan can select an upcoming FBS game and, where licensed verified data exists, see our independent model's supported predictions beside timestamped market observations; review ATS/totals and team historical context; understand movement, data quality and uncertainty; inspect source/methodology and historical evaluation; and make their own judgment without being told what to bet. No fabricated information, no unauthorized data use, no regression in the football app, and production tests passed.

**Stop rule:** complete V7 as one coherent release. Do not spin up V7.1/V8, replace the incumbent prediction engine, build trading integrations or widen provider scope merely because it is possible.

## Beta and development sequencing
- During the current beta: research feasibility, verify sources and record fan feedback. Do not modify live V6 for V7.
- After beta review: incorporate only directly relevant findings and execute M1–M7 in substantial end-to-end passes.
- If a source is unavailable or licensing fails: report the gap and reduce to the smallest truthful feature set; never substitute synthetic data or endless research loops.
- PR for this roadmap is documentation-only and must not be merged without owner approval.
