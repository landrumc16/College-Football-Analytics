# Version 7 — Milestone 1: Research and data feasibility (final)

**Date:** November 16, 2026.
**Branch / PR:** `v7-market-intelligence-roadmap`, PR #32.
**Baseline `main`:** `5a6fd8d8dda02f9c61c81248f31b0648c39e6968`.
**Scope:** research and read-only verification only. No V7 app code, no data
ingestion into the app, no production change, no merge.

## Milestone 1 verdict

**Internal research and verification are complete.** Two items now depend on third
parties:

- **Kalshi** must grant written permission before any Market Watch display.
- **CFBD** is asked to confirm one point: how much per-game line data a public
  static site may publish. This is a clarification, not a blocker.

**Readiness:**
- **Historical spread/ATS/totals work (CFBD): ready for Milestone 2.**
- **Kalshi Market Watch: blocked pending authorization.**

| # | Completion criterion | Result |
| --- | --- | --- |
| 1 | CFBD samples retrieved and checked against existing results | **Met.** 20 live calls; 8,633 games matched with 100% name and score agreement (§3). |
| 2 | Coverage and missing-data limits documented | **Met** (§3). |
| 3 | CFBD redistribution confirmed or explicitly unresolved | **Met.** Display and derived outputs are permitted; one scope question goes to CFBD (§4). |
| 4 | Kalshi capabilities checked against read-only samples | **Met** (§5). |
| 5 | Kalshi display rights established or classified | **Met.** Written permission is required; Market Watch is blocked (§6). |
| 6 | Model compatibility verified | **Met** (§7). |
| 7 | Architecture and costs documented | **Met** (§8, §9). |
| 8 | Ready vs. blocked features identified | **Met** (§10). |

Status labels:
- **VERIFIED AVAILABLE:** confirmed in repository code or data, or by live
  retrieval in this milestone.
- **AVAILABLE WITH RESTRICTIONS:** retrievable, but limited by licence, coverage
  or quality.
- **UNVERIFIED:** documented but not confirmed.
- **UNAVAILABLE:** does not exist or cannot be used.

## 1. Evidence produced

| Evidence | Where |
| --- | --- |
| CFBD `/lines` sample: 2016–2025 regular and postseason, 20 API calls through the existing `CFBD_API_KEY` secret, joined to `research/archive/verified/espn-games.json.gz` | Workflow `.github/workflows/v7-cfbd-lines-sample.yml`, script `scripts/v7_cfbd_lines_sample.py`, [run 43865079391](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43865079391) at `29a2441`. The run logs aggregates and 12 hand-check games only; raw responses were never stored. |
| Kalshi read-only public API samples (no account; about 15 requests on 2026-11-16) | Reported below. Responses were kept only in a temporary scratch area and deleted, consistent with Developer Agreement §3.1. |
| CFBD Terms of Use, full text (effective Aug. 12, 2026) | https://collegefootballdata.com/terms |
| Kalshi Developer Agreement v1.1, full text | https://kalshi-public-docs.s3.amazonaws.com/Kalshi-Developer-Agreement.pdf |
| Kalshi Data Terms of Use, full text | https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf |
| Kalshi rate limits and historical data docs | https://docs.kalshi.com/getting_started/rate_limits , https://docs.kalshi.com/getting_started/historical_data |

## 2. Existing reusable resources (VERIFIED AVAILABLE)

- **Results archive:** 2016–2025, ESPN-ID keyed and independently corroborated
  (`research/archive/verified/espn-games.json.gz`; 8,635 FBS-participant games).
  CFBD game IDs equal these IDs, so lines join directly; no new game database is
  needed.
- **Incumbent model outputs:** `home_margin` and `home_win_probability` in
  `data/season-2026-report.json`.
- **2026 pregame ledger:** `data/pregame-2026-history.json`.
- **Team aliases:** in `pipeline.py` and `report.py`.
- **Spread-conversion helper:** in `model.py`.
- **Market benchmark protocol:** `docs/V2-SPREADSHEET-MARKET-BENCHMARK.md`.
- **Pipeline:** the refresh workflow, atomic snapshots and static Pages
  publishing.

## 3. CFBD historical lines — live verification results

The join uses the CFBD game ID, which is the ESPN event ID. All counts are
FBS-participant games in our archive.

| Season | Archive games | Matched | Names / scores agree | With a closing spread | With an opening spread | With a closing total | With an opening total | ATS pushes | O/U pushes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | 873 | 873 | 873 / 873 | 866 | 0 | 760 | 0 | 21 | 0 |
| 2017 | 874 | 874 | 874 / 874 | 873 | 0 | 785 | 0 | 23 | 8 |
| 2018 | 884 | 884 | 884 / 884 | 869 | 0 | 851 | 0 | 20 | 8 |
| 2019 | 888 | 888 | 888 / 888 | 881 | 0 | 881 | 0 | 18 | 14 |
| 2020 | 570 | 568 | 568 / 568 | 567 | 0 | 567 | 0 | 9 | 8 |
| 2021 | 887 | 887 | 887 / 887 | 887 | 878 | 887 | 879 | 13 | 8 |
| 2022 | 896 | 896 | 896 / 896 | 892 | 818 | 892 | 823 | 14 | 12 |
| 2023 | 910 | 910 | 910 / 910 | 907 | 849 | 907 | 851 | 14 | 11 |
| 2024 | 919 | 919 | 919 / 919 | 904 | 861 | 903 | 861 | 16 | 10 |
| 2025 | 934 | 934 | 934 / 934 | 934 | 934 | 934 | 934 | 8 | 1 |
| **Total** | **8,635** | **8,633** | **100% / 100%** | **8,580 (99.4%)** | **4,340 (2021+ only)** | **8,367 (96.9%)** | **4,348 (2021+ only)** | | |

**Findings:**

- **Closing spreads, 2016–2025: VERIFIED AVAILABLE.** 99.4% of FBS-participant
  games have one.
  - **Join quality:** 8,633 of 8,635 games matched by ID. Both team names and
    both scores agree with our independently corroborated archive for all
    8,633.
  - **Correct calculations:** ATS and over/under results compute correctly from
    our archived scores. 12 Texas Tech games from 2016 were hand-checked against
    the archive; all scores and sign conventions agree.
  - **Two gaps:** 2 archive games from 2020 are missing in CFBD, and 53 matched
    games have no line.
- **Closing totals: VERIFIED AVAILABLE.** 96.9% of games. In 2016–2019 the
  `consensus` row often has no total, so a provider-fallback rule is required:
  with consensus only, 7,586 games are computable.
- **Opening spreads and totals: AVAILABLE WITH RESTRICTIONS.** They exist only for
  **2021–2025** (about 94% of those games) and are **absent for 2016–2020**.
  Opening-to-close movement must show N/A before 2021. "Open" means the
  provider's first value, not a market-wide open.
- **Intraday movement: UNAVAILABLE from CFBD.** Only open and close values exist.
- **Provider coverage changes over time: AVAILABLE WITH RESTRICTIONS.**

  | Seasons | Providers |
  | --- | --- |
  | 2016–2017 | consensus, teamrankings, numberfire |
  | 2018–2020 | adds Caesars and Bovada |
  | 2021–2022 | consensus, Bovada, William Hill (NJ) |
  | 2023 | Bovada, DraftKings, ESPN Bet, William Hill; consensus nearly gone (29 games) |
  | 2024–2025 | DraftKings, Bovada, ESPN Bet only |

  No single provider spans all 10 seasons. M2 needs a documented, per-game
  recorded selection rule. Suggested order: consensus, then DraftKings, Bovada,
  ESPN Bet, William Hill, Caesars, teamrankings, numberfire.
- **Data-quality caveat (provider disagreement).** In the hand-checks, 2016
  `consensus` sometimes disagrees materially with the other two providers:
  - Texas Tech vs. West Virginia: consensus −1 vs. +3 / +3;
  - Arizona State vs. Texas Tech: consensus −5 vs. +1.5 / +1.

  M2 must therefore record which provider was used, flag disagreements of 3 or
  more points, and show the provider beside every historical line.
- **Moneylines:** fields exist (`homeMoneyline`, `awayMoneyline`). Coverage was
  not measured; they are not required for the minimum product.
- **API fields observed:** `id`, `season`, `week`, `seasonType`, `startDate`,
  team/score/conference/classification fields; per line `provider`, `spread`,
  `formattedSpread`, `spreadOpen`, `overUnder`, `overUnderOpen`,
  `homeMoneyline`, `awayMoneyline`.

## 4. CFBD licensing (full official terms, effective Aug. 12, 2026)

> **Update (2026-11-16):** the clarification requested below was answered in writing by a CFBD
> administrator. One provider's closing spread and closing total per FBS game since 2016, with
> the provider named, may be shown in browser JSON supporting team and game pages, but never as a
> standalone dataset, bulk download or data feed. See `docs/V7-LICENSING.md`.

**Relevant text:**

| Section | Text |
| --- | --- |
| Front matter | "Commercial use is permitted." |
| §4 Commercial Use and Permitted Uses | You may "use API Data in free or paid websites, applications, dashboards…"; "privately cache, store, normalize, and retain API responses"; "**display reasonable portions of factual API Data as part of a larger product**"; "perform historical analysis, backtesting…"; and "**publish and commercialize independently created analyses … rankings, visualizations, and other Derived Outputs**". |
| §1 Definitions | **Redistribution** is "providing API Data itself to a third party as a standalone dataset, bulk download, raw feed, database mirror, substitute API…". "Reasonable display and ordinary exports permitted by Section 4 are not Redistribution." |
| §5 Prohibited Redistribution | You may not "publish, or provide API Data as a standalone dataset or bulk download"; "operate a raw feed, public database mirror, proxy, substitute API"; or "expose … an API key in public or client-side code". |
| §6 Attribution | Optional; recommended wording "Data provided by CollegeFootballData.com." |
| §10 Betting-related uses | Permitted, subject to law; CFBD does not endorse any sportsbook. |

**What this means for our free public app:**

| Display | Status |
| --- | --- |
| Derived ATS records, derived O/U records, team-level betting statistics (cover rates, splits, average cover margin) | **Permitted.** These are Derived Outputs. |
| Historical spreads and totals shown for a game or team's schedule inside the app | **Permitted** as "reasonable portions of factual API Data as part of a larger product". |
| A complete per-game line archive (all games, all providers, every season) as one publicly fetchable static JSON file | **Unresolved; do not do this.** On GitHub Pages every app data file is publicly downloadable, so a complete archive file could function as a "standalone dataset or bulk download". |
| Raw responses, a mirror or exposing the key | **Prohibited.** The key already stays in Actions secrets. |

**Design rule for M2:**
- Publish derived records.
- Publish per-game lines only in the slices the UI needs: one closing spread and
  total per game, with the provider named. Split them per team and season, not
  as one bulk file.
- Never publish raw provider-level responses.
- Show the attribution.

**Clarification to request from CFBD** (via the contact address on the terms page
or their Discord):

> "Our free, no-account site is statically hosted, so the JSON files the browser
> loads are technically downloadable. Is it acceptable under §4 and §5 to publish
> one closing spread and total per FBS game (2016–present, provider named),
> split into per-team files, plus derived ATS/O-U records? Or should per-game
> lines be limited to a narrower window?"

This does not block M2: derived records alone are clearly permitted.

## 5. Kalshi API — confirmed behaviour (live, read-only, no account)

| Capability | Status | Evidence (2026-11-16) |
| --- | --- | --- |
| Public market data without authentication | **VERIFIED AVAILABLE** (technical) | `GET /trade-api/v2/series/KXNCAAFGAME` and `/markets?series_ticker=KXNCAAFGAME&status=open` returned 200 without credentials. |
| College football market discovery | **VERIFIED AVAILABLE** (technical) | Game winner `KXNCAAFGAME` (200+ open markets, paginated). The series list includes `KXNCAAFSPREAD` (spread ladder, e.g. "Fresno St. wins by over 50.5 points"), `KXNCAAFTOTAL`, `KXNCAAFTEAMTOTAL`, quarter/half markets and futures. |
| Current prices | **VERIFIED AVAILABLE** (technical) | Fields `yes_bid_dollars`, `yes_ask_dollars`, `last_price_dollars`, `no_*`. Example: Miami (FL) vs. Virginia Tech, Miami yes bid 0.89 / ask 0.92 / last 0.92. |
| Volume and open interest | **VERIFIED AVAILABLE** (technical) | `volume_fp`, `volume_24h_fp`, `open_interest_fp` per market. |
| Bid-ask size and order book | **VERIFIED AVAILABLE** (technical) | `yes_bid_size_fp`, `yes_ask_size_fp`; `GET /markets/{ticker}/orderbook?depth=5` returned 200 without authentication, with 5 price levels per side. **Current only.** |
| Historical prices (candlesticks) | **VERIFIED AVAILABLE** (technical) | Live market: `/series/…/markets/{t}/candlesticks?period_interval=60` (valid values 1, 60, 1440). Settled 2025 market: `/historical/markets/KXNCAAFGAME-26JAN01ORETTU-TTU/candlesticks` returned 167 hourly candles with OHLC bid, ask and trade price, volume and open interest. |
| Historical trades (actual transactions) | **VERIFIED AVAILABLE** (technical) | `/historical/trades?ticker=…` returned individual trades (`count_fp`, `yes_price_dollars`, `taker_side`, `created_time`). |
| Coverage from 2025 | **VERIFIED AVAILABLE** (technical) | `/historical/markets?series_ticker=KXNCAAFGAME` returned 2,532 settled markets (1,266 game events) between 2025-07-01 and the cutoff, 1,868 of them from the 2025 season. Median volume about 540k contracts (10th percentile 32k; 90th percentile 5.6M). |
| Historical cutoff | **VERIFIED AVAILABLE** | `GET /historical/cutoff`: `market_settled_ts` and `trades_created_ts` = 2026-09-17; `orders_updated_ts` = 2026-11-02. Data newer than the cutoff is served from live endpoints. |
| Historical order-book depth | **UNAVAILABLE** | Not offered; it would exist only if snapshots were captured going forward. |
| Matching to our games | **AVAILABLE WITH RESTRICTIONS** | 859 of 936 (92%) 2025-season events matched our archive using simple name normalization. The misses are aliases (NC State, San José State, FIU, ULM, UMass) or non-archive FCS games, so an alias table is needed. Kickoff time must come from our archive: `occurrence_datetime` is empty on historical markets. |
| Rate limits and authentication | **AVAILABLE WITH RESTRICTIONS** | Official docs use a token-bucket model per tier, and unauthenticated public requests have separate, undisclosed limits. We received **HTTP 429 after about 5 rapid unauthenticated calls**; with 2–3 s spacing the calls succeeded. Cacheable responses carry no rate-limit headers. Any production collector needs backoff and low call volume. |
| **In-game trading** | **Important constraint** | Game markets trade until the game ends (the Oregon–Texas Tech market closed after the final, last price 0.01). Last price and close are therefore post-result, not pregame. Pregame comparisons must use the last candle **before kickoff**. |

## 6. Kalshi public-display rights (full official terms)

- **Developer Agreement v1.1, §3:** "Use of Kalshi APIs is expressly limited to
  facilitating a members own trading on the Exchange; all other usages are
  disallowed." §3.1 prohibits "Collecting, caching, aggregating, or storing data
  or content accessed via the API except for purposes of facilitating your own
  trading on Kalshi. You may not share such data or content with third parties
  in any manner without prior written authorization from Kalshi."
- **Data Terms of Use, Part I:** "You may access content only for your personal use
  for non-commercial purposes", excluding "providing archived or cached data sets
  containing Kalshi Data". Without prior written authorization it prohibits
  "publicly displaying, publishing … compiling … systematic retrieval to create
  collections … databases".

**Classification:** public display, caching, aggregation and redistribution of
Kalshi data by our app is **UNAVAILABLE without Kalshi's prior written
authorization**. Kalshi Market Watch is **BLOCKED pending authorization**.

- **No Kalshi data is stored in the repository or published.**
- The read-only samples above were limited to feasibility verification, which §3
  does not expressly cover. **No further Kalshi API collection should occur until
  permission is granted.**

The draft permission request is in the Appendix. It has not been sent.

## 7. Model compatibility (VERIFIED AVAILABLE)

- **Projected margin and win probability:** all 212 current predictions satisfy
  `home_win_probability = 1/(1+10^(−home_margin/18))` exactly (model
  `workbook_2026_baseline`, home-field advantage 3.0).
- **Authentic 2026 pregame forecasts:**
  - The ledger has 858 entries; **838** have full provenance
    (`source_retrieved_at`, `forecast_recorded_at`, `scheduled_kickoff_at`).
  - Of those, **256 are FBS vs. FBS**, all from weeks 10–13 only, because
    archiving began in November 2026.
  - These, plus the 65 independently verified FBS games, are the only authentic
    pregame comparisons available.
  - **2016–2025 model results are retrospective replays** and must always be
    labelled that way.
- **Spread-to-probability conversion** (`model.py`
  `market_home_win_probability`, scale 19.5): tested on **7,560** FBS-vs-FBS
  2016–2025 games, using the selected closing spread against actual winners.

  | Scale | Brier | Log loss |
  | --- | --- | --- |
  | 19.5 (current) | **0.17477** | 0.51986 |
  | 20.5 (best by log loss) | 0.17468 | 0.51967 |
  | 15 | 0.17741 | 0.53084 |
  | 25 | 0.17564 | 0.52356 |

  **Conclusion:** 19.5 is within 0.0002 log loss of the best scale in this
  sample, so it is **suitable for V7 as a labelled approximation** of
  spread-implied win probability. Show it as "spread-implied", not as a
  market-quoted price.
- **Not available:** a model projected total. No total model will be created, so
  model-vs-total comparisons are **UNAVAILABLE**. Descriptive over/under records
  remain available.

## 8. Architecture recommendation

Extend the existing scheduled pipeline and static Pages site. **No new backend.**

1. **M2 historical backfill:**
   - Pull CFBD `/lines` once per season and season type, about **20 calls**, into
     private checksummed snapshots in the pipeline (cache and store are
     permitted).
   - Normalize by game ID against the verified archive.
   - Apply the documented provider-selection rule and disagreement flags.
   - Publish only derived per-team ATS/O-U records and per-team, per-season
     closing lines.
2. **Current season:** add the lines pull to the existing refresh workflow (a
   few calls per run). Reuse the atomic write, last-good retention and stale
   banner, and add completeness checks (QA finding D1) so a partial lines
   response cannot publish.
3. **Kalshi:** nothing until written permission arrives. If granted:
   - a low-frequency snapshot job (respecting 429 and backoff), with pregame cut
     at kickoff;
   - published as timestamped snapshots, not live prices, because GitHub Actions
     scheduling showed 4–8 hour gaps.

## 9. Costs (realistic)

| Item | Cost |
| --- | --- |
| CFBD | The backfill is about 20 calls, and the current season adds a few calls per refresh. The **free tier (1,000 calls/month)** is sufficient; $1–$5/month Patreon only for headroom. |
| Kalshi | $0 API fees; display licence terms unknown until Kalshi replies. |
| Hosting and CI | $0 extra (public repo, Pages, Actions). |
| Paid intraday odds (The Odds API) | Not needed for the minimum product. |
| **Total** | **$0/month** for the minimum product (optionally $1–$5). |

## 10. Minimum complete V7 product — ready vs. blocked

| Feature | Status |
| --- | --- |
| Team Market History (2016–2025 + current): ATS overall and by season, home/away, favourite/underdog, last 5/10/20, O/U records, cover margin, pushes, coverage counts, provider named | **READY for M2** (VERIFIED AVAILABLE; derived outputs permitted) |
| Game detail: model projected margin vs. closing/current spread; model win probability vs. spread-implied probability (scale 19.5, labelled) | **READY for M2** |
| Historical validation: authentic 2026 ledger vs. closing lines (256 FBS games, small sample); 2016–2025 retrospective replay vs. closing lines (labelled) | **READY for M2** |
| Opening-to-closing movement | **READY, 2021–2025 only**; N/A for 2016–2020 |
| Learn & Research explainers | **READY** |
| Per-game historical line display beyond team/schedule views | **Pending CFBD clarification** (§4); derived records are unaffected |
| Kalshi Market Watch (prices, volume, open interest, spread, history) | **BLOCKED** pending Kalshi written authorization |
| Intraday sportsbook movement | **Deferred / UNAVAILABLE** from CFBD |
| Model-vs-total comparison | **UNAVAILABLE** (no total model) |
| Historical order-book depth | **UNAVAILABLE** |

## Appendix — Kalshi permission request (draft; **not sent**, needs owner approval)

> **Subject:** Request for written authorization to display Kalshi college football
> market data — College Football Analytics (educational, non-wagering)
>
> Hello Kalshi team,
>
> I run College Football Analytics (https://landrumc16.github.io/College-Football-Analytics/),
> a free, no-account, educational website for college football fans. It
> publishes independent team ratings, game forecasts and historical analysis.
> It does not accept wagers, execute trades, link accounts, or provide betting or
> trading recommendations.
>
> Under Section 3.1 of the Kalshi Developer Agreement and the Kalshi Data Terms of
> Use, I am requesting prior written authorization to display limited Kalshi
> market information alongside our model's forecasts in an educational "Market
> Watch" section:
>
> - **Markets:** KXNCAAFGAME game-winner markets for FBS games, and optionally
>   KXNCAAFSPREAD / KXNCAAFTOTAL.
> - **Fields:** yes bid, yes ask, last traded price, volume, open interest, and a
>   timestamp, with Kalshi named as the source.
> - **Update frequency:** periodic snapshots, about every 30–60 minutes on game
>   days and a few times daily otherwise, using the public REST API with
>   backoff. No streaming.
> - **History:** pregame price history (hourly candles up to kickoff) for the
>   current and previous seasons. Retention for the life of the educational
>   archive, or a period you specify.
> - **No raw dataset, bulk download, data feed or resale.** Data is shown only in
>   our app's charts and tables.
> - **No trading, account creation or recommendations.** We add clear
>   educational disclaimers.
>
> Please let me know whether this use can be authorized, any conditions
> (attribution, delay, retention or display limits), and whether a separate data
> licence is required.
>
> Thank you,
> [Owner name], College Football Analytics
