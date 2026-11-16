# Version 7 — Milestone 1: Research and data feasibility

Date: November 16, 2026. Branch: `v7-market-intelligence-roadmap` (PR #32).
Baseline `main`: `5a6fd8d8dda02f9c61c81248f31b0648c39e6968`. This branch adds only
data refreshes and planning documents.
Scope: research only. No V7 code, data ingestion, production change or merge.

**Bottom line**

1. Historical **spreads and totals** for 2016–2025 appear obtainable through the
   CFBD API we already use, but per-season coverage is unverified until a sample
   is pulled. Its terms permit commercial use; the redistribution clauses still
   need to be read in full.
2. **Kalshi** college football game markets exist only since the 2025 season.
   Market data is technically retrievable, but Kalshi's data terms appear to
   **prohibit public display or redistribution without written consent**.
3. Our model already publishes the two outputs a market comparison needs:
   **projected margin** and **win probability**. Only the 2026 forecasts are
   authentic archived pregame predictions; 2016–2025 are retrospective replays.
4. **Milestone 1 is not yet complete.** The roadmap requires samples retrieved and
   verified from each selected source. Live retrieval failed in this session
   (§9), so no sample has been verified. Milestone 2 (the CFBD-based archive)
   should wait for those samples and the CFBD redistribution check. Kalshi's
   answer on display rights gates only Market Watch.

Status labels used below: **VERIFIED AVAILABLE**, **AVAILABLE WITH RESTRICTIONS**,
**UNVERIFIED** and **UNAVAILABLE**. VERIFIED AVAILABLE is used only for
resources confirmed directly in repository code or data. External capabilities
are based on search excerpts of the official pages linked below, plus clearly
labelled secondary sources; no external page or endpoint was opened directly in
this session. External items are therefore at most AVAILABLE WITH RESTRICTIONS
until a live sample confirms them.

## 1. Existing reusable resources (inspected in the repository)

| Resource | Location | V7 use | Status |
| --- | --- | --- | --- |
| Incumbent model outputs: `home_margin`, `home_win_probability` and predicted winner for every upcoming game | `data/season-2026-report.json`, `src/cfb_analytics/pipeline.py`, `predictions.py` | Model side of the comparison: margin vs. spread, probability vs. market-implied probability. No new model is needed. | VERIFIED AVAILABLE |
| Immutable 2026 pregame forecast ledger: 858 entries with `forecast_recorded_at` and kickoff provenance | `data/pregame-2026-history.json`, `forecast_ledger.py` | The only **authentic** archived model forecasts. Usable for honest 2026 comparisons where a market quote with an earlier timestamp exists. | VERIFIED AVAILABLE |
| Independently verified published-forecast subset: 65 FBS-vs-FBS games (2026 weeks 10–11) | `web/public/v5-forecast-evaluation.json` | Small authentic validation sample. Too small for strong conclusions. | VERIFIED AVAILABLE |
| 2016–2025 results archive and retrospective replay: 3,059 games in the challenger research and 3,174 in the V2 walk-forward | `web/public/v5-historical-results.json`, `v6-prediction-research.json`, `data/v2-research-summary.json` | Game identities and outcomes for joining historical lines. Model replays are **retrospective, not authentic pregame**, and must be labelled that way. | VERIFIED AVAILABLE (retrospective) |
| Team identity normalization and aliases (e.g. `Miami` → `Miami (FL)`) | `pipeline.py`, `report.py`, `forecast_ledger.py` | Joining CFBD lines and Kalshi tickers to our games. The alias gap in polls (QA finding D4) shows normalization must be applied at every ingestion point. | VERIFIED AVAILABLE |
| Spread-to-probability conversion `1/(1+10^(spread/19.5))` and an existing slot for a closing spread | `model.py:70`, `predictions.py`, `workbook_prediction.py` | Converting a spread to an implied win probability for comparison. The 19.5 scale comes from the spreadsheet and must be validated before V7 relies on it. | VERIFIED AVAILABLE (needs validation) |
| Market benchmark protocol: same-intersection comparison, MAE/RMSE for margin, Brier/log loss for probability, no cover rate as winner accuracy | `docs/V2-SPREADSHEET-MARKET-BENCHMARK.md` | The evaluation design for M6 already exists. | VERIFIED AVAILABLE |
| CFBD API client, refresh workflow, `CFBD_API_KEY` secret, atomic snapshots, scheduled Actions, static Pages publishing | `refresh.py`, `.github/workflows/refresh-data.yml`, `dashboard.yml` | Reuse the same pipeline for lines and market snapshots. No backend needed. | VERIFIED AVAILABLE |

**Do not rebuild:** game results, team identities, model outputs, the forecast
ledger or the evaluation protocol. Historical lines must be **joined** to the
existing archive, not acquired as a second game database.

## 2. Data providers and official sources

| Provider | What it offers | Access | Official source |
| --- | --- | --- | --- |
| **CollegeFootballData (CFBD)** — recommended | `GET /lines`: per-game spread, total, moneylines and opening values by provider | API key (we already hold one). Free tier about 1,000 calls/month; Patreon tiers from $1/month. | [Terms](https://collegefootballdata.com/terms), [API tiers](https://collegefootballdata.com/api-tiers), [usage and access](https://apinext.collegefootballdata.com/usage-and-access), [data availability](https://apinext.collegefootballdata.com/data-availability) |
| **Kalshi** — prediction market | `KXNCAAFGAME` game markets, plus spread, total and team-total ladders; market, trade and candlestick endpoints, and a historical archive behind a cutoff | Market-data reads are reported as public; trading and some depth need an API key. The Developer Agreement applies on first API use. | [Historical data](https://docs.kalshi.com/getting_started/historical_data), [rate limits](https://docs.kalshi.com/getting_started/rate_limits), [historical trades](https://docs.kalshi.com/api-reference/historical/get-historical-trades.md), [Developer Agreement](https://kalshi-public-docs.s3.amazonaws.com/Kalshi-Developer-Agreement.pdf), [Data Terms](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf) |
| **The Odds API** — paid fallback | Historical odds snapshots (featured markets from June 2020; 10-minute intervals, 5-minute from Sept. 2022); NCAAF history on paid plans | Paid credits; historical calls cost about 10× normal | [Historical odds](https://the-odds-api.com/historical-odds-data/), [NCAAF](https://the-odds-api.com/sports/ncaaf-odds.html), [v4 docs](https://the-odds-api.com/liveapi/guides/v4/) |
| Polymarket — not recommended | Public Gamma/CLOB reads with price history per token. College football coverage was not confirmed. Its US exchange is a separate venue. | Public reads | [Docs](https://docs.polymarket.com/api-reference) |
| SportsDataIO, OddsPapi, SportsGameOdds — not recommended | Commercial odds feeds | Paid contracts | Not evaluated further: they offer no advantage over CFBD for history or over Kalshi for prediction markets |
| Free websites (Stick to the Model, SportsOddsHistory, legacy forum spreadsheets) — **rejected** | Scraped or uncredited closing lines | Unclear licence and provenance | No verifiable source, licence or capture time. Not acceptable under the "no unverified data" rule. |

## 3. Historical data coverage

| Capability (2016–2025 unless noted) | Source | Status | Notes |
| --- | --- | --- | --- |
| Closing point spread per FBS game | CFBD `/lines` | **UNVERIFIED** (strong secondary evidence) | Third-party reviews report CFBD history from 2013 with per-game, per-provider coverage that varies. Coverage per season must be measured from a real pull before any claim. |
| Opening spread and total | CFBD `/lines` (opening fields) | **UNVERIFIED** | cfbfastR documents an opening over/under and moneylines. Opening-spread availability by provider and season is unconfirmed. "Open" means the provider's first captured value, not a market-wide open. |
| Closing over/under | CFBD `/lines` | **UNVERIFIED** | Same basis as spreads. |
| ATS results, home/away, favourite/underdog, O/U records, cover margin | Derived from lines plus our verified results archive | **AVAILABLE WITH RESTRICTIONS** | Pure calculation once lines exist. Pushes and missing lines must stay explicit. Limited by line coverage. |
| Intraday line movement | The Odds API (paid; NCAAF start date unconfirmed, featured markets from mid-2020) | **AVAILABLE WITH RESTRICTIONS** (cost); **UNAVAILABLE** before 2020 | CFBD offers only open and close points. Full movement history would need a paid feed and would still not cover 2016–2019. |
| Consensus vs. per-book lines | CFBD providers (documented values include Caesars, consensus, numberfire, teamrankings) | **UNVERIFIED** | The provider list changes over the years. Pick one stated provider rule (for example consensus, else a named fallback) and record it per game. |
| Kalshi college football game markets | Kalshi | **AVAILABLE WITH RESTRICTIONS** | Only from the **2025 season** (moneyline from launch; spread and total self-certified Aug. 25, 2025). No 2016–2024 history exists. |
| Kalshi historical prices (candlesticks) and trades | Kalshi `/historical/*` behind `GET /historical/cutoff` | **AVAILABLE WITH RESTRICTIONS** | Technically documented. Separate cutoffs for settled markets, trades and orders, and they move forward. Display rights are not granted (§4). |
| Historical Kalshi order-book depth | — | **UNAVAILABLE** | Not provided historically. It can only exist if we capture snapshots ourselves going forward, and the licence would also have to permit that. |

## 4. Licensing and redistribution

- **CFBD — AVAILABLE WITH RESTRICTIONS.**
  - The official terms (effective Aug. 12, 2026) permit commercial use on every
    tier. Attribution is requested but optional ("Data provided by
    CollegeFootballData.com").
  - Secondary summaries say the terms bar reselling raw data as a bulk download
    or substitute API.
  - The **redistribution clauses were not read in full** (fetch blocked). Before
    M2, confirm that publishing derived per-game lines and ATS records on a free
    public site is allowed.
  - Recommended publication shape: derived records and the lines needed per game,
    with no bulk raw dump.
- **Kalshi — blocker for public display.**
  - The Developer Agreement binds every API user. Secondary sources describe a
    §3.1 restricting collecting, caching, aggregating or storing API data except
    for one's own trading, and sharing it with third parties without prior
    written authorization. One summary instead says v1.1 is silent on data.
  - The Kalshi Data Terms of Service limit website content to personal,
    non-commercial use and exclude archived or cached datasets and AI/ML use
    without written consent.
  - Kalshi licenses institutional data distribution commercially (LO:TECH).
  - **Conclusion:** displaying Kalshi prices, volume or history on our public
    site is **not permitted unless Kalshi grants written permission**. Its
    endpoints being public is not a licence.
  - **Action:** the owner contacts Kalshi for written display permission and its
    terms.
- **The Odds API — AVAILABLE WITH RESTRICTIONS.** It is a paid commercial licence.
  Display and redistribution terms must be checked in the plan agreement before
  purchase. Not needed if CFBD coverage is sufficient.
- **Free scraped archives — UNAVAILABLE.** No licence or provenance.

## 5. Kalshi API capabilities and limitations

| Capability | Status | Detail |
| --- | --- | --- |
| Discover college football game markets | AVAILABLE WITH RESTRICTIONS | Series `KXNCAAFGAME`, with tickers like `KXNCAAFGAME-26OCT03LOUNCST` (date plus team codes). Team codes need a mapping table to our canonical names. |
| Current prices (yes/no bid, ask, last) and volume and open interest per market | AVAILABLE WITH RESTRICTIONS | Documented market fields. Reads are reported as needing no key. **Live call not verified in this session.** |
| Bid-ask spread and liquidity (order book) | AVAILABLE WITH RESTRICTIONS | `GET /markets/{ticker}/orderbook`. Sources conflict on whether it needs authentication. Depth is current-only. |
| Historical prices | AVAILABLE WITH RESTRICTIONS | Candlesticks via `period_interval`, with a batch route for up to 100 tickers. Older settled markets are served from `/historical/markets/{ticker}/candlesticks`. |
| Historical trades (actual transactions) | AVAILABLE WITH RESTRICTIONS | `/historical/trades` before the cutoff. These are executed trades, unlike quotes. |
| Historical order-book depth | UNAVAILABLE | Never served historically. |
| Rate limits | AVAILABLE WITH RESTRICTIONS | A token-bucket model by tier (Basic, Advanced and higher). Exact Predictions budgets come from `GET /account/limits`, so they were **unverified** here. Older docs listed about 10–20 reads/s at Basic. A few hundred calls per refresh is far below any tier. |
| Historical coverage | AVAILABLE WITH RESTRICTIONS | College football begins with the 2025 season, so only the 2025–2026 seasons exist. |
| Licence to display | **UNAVAILABLE without written consent** | See §4. |

**Measures to keep separate:**
- **Last trade** is a transaction.
- **Bid and ask** are quotes; their midpoint is a market-implied estimate, and a
  wide spread means low confidence in it.
- **Volume** counts contracts traded and **open interest** counts outstanding
  contracts. Neither is a share of people or of money on a side.
- Kalshi prices include no vig, but trading fees apply.
- Spread and total contracts are threshold ladders ("wins by more than X"), so
  they are not directly a single sportsbook line.

## 6. Model compatibility

**Already exists (no new model):**
- Projected home margin. Compare it with the spread (sign convention: negative
  home spread means the home team is favoured) using MAE/RMSE and the share of
  games where the model and the spread pick different sides.
- Model win probability. Compare it with market-implied probability using Brier,
  log loss and calibration on the same game sample.

**Needs validation before display:**
- The 19.5 spread-to-probability scale.
- Any vig removal for moneylines.
- Mapping Kalshi spread and total ladders to a single implied line.
- Whether "model disagreement" thresholds carry information.

**Does not exist and must not be invented:**
- A model projected **total**. The incumbent outputs margin and win probability
  only, so model-vs-total comparisons are **UNAVAILABLE** unless a total model is
  separately approved. Descriptive over/under records are still available.

**Avoiding hindsight bias:**
- **2026:** the ledger's `forecast_recorded_at` must be earlier than the market
  observation time, which must be earlier than kickoff. Use closing lines for
  "market at close" and the quote with the latest earlier timestamp for matched
  comparisons.
- **2016–2025:** model forecasts are retrospective walk-forward replays. Label
  every result "retrospective replay vs. historical closing line", never
  "authentic pregame prediction".
- Use the same intersection of games for model and market. Report coverage and
  confidence intervals, and no profitability claims without executable-price
  evidence (roadmap M6).

## 7. Technical architecture recommendation

Extend what already exists. **No new backend.**

1. **Historical lines (one-off backfill):**
   - The scheduled pipeline pulls CFBD `/lines` by season and week into
     immutable, checksummed snapshots, with provenance and coverage reports.
   - Join to the existing results archive by CFBD game ID.
   - Publish small derived JSON (per-team ATS and O/U splits, per-game close
     lines) alongside the existing `web/public/*.json`.
2. **Current lines:** add a lines pull to the existing refresh workflow, once
   daily plus before kickoff windows.
3. **Kalshi, only if permission is granted:**
   - A separate scheduled job snapshots open `KXNCAAFGAME` markets for that
     week's games (price, bid, ask, volume, open interest, timestamp) every
     30–60 minutes on game days.
   - Settled-market candlesticks fill in the history.
   - Retain only what the licence permits.
4. **Publishing:**
   - Static GitHub Pages and JSON stay as they are.
   - The existing PWA rule stays: live JSON is never cached.
   - Stale banners use the existing 72-hour pattern, with a shorter threshold for
     market data.
5. **Failure handling:**
   - Reuse the atomic write with last-good retention.
   - Add the completeness and regression checks proposed in the final pre-beta QA
     (finding D1), so a partial lines or market response cannot publish.
6. **Constraint:** GitHub Actions scheduling is unreliable for frequent jobs.
   QA observed 4–8 hour gaps against a 15-minute cron. Market Watch must
   therefore be presented as **periodic snapshots with timestamps, not live
   prices**. True live data would need a server or a client-side call, which the
   licence most likely forbids.

**Storage estimates (assumptions, not measurements):**
- CFBD lines for 10 seasons: about 8,000 FBS games × a few providers ≈ 5–15 MB
  raw. Derived public JSON is under 1 MB.
- Kalshi snapshots: about 60 FBS games/week × about 6 markets × 30 snapshots ≈
  10–20k rows/week, roughly 5–10 MB per season raw.

All of this fits comfortably in the repository and in Pages limits.

## 8. Estimated ongoing costs (published list prices; not verified invoices)

| Item | Estimate |
| --- | --- |
| CFBD | The 10-season backfill is roughly 1 call per season-week, about 160 calls; each refresh adds calls. Free tier (1,000/month) may suffice; **$1–$5/month Patreon** (5,000–30,000 calls) gives headroom. Confirm on the official tiers page. |
| Kalshi | $0 in API fees for market data reads. **Display licence: unknown, pending Kalshi's answer.** |
| The Odds API (only if intraday movement is required) | Third-party listings show paid plans of about **$30–$249/month**, with historical calls at about 10× credits. Not recommended for the minimum release. |
| Hosting and CI | $0 extra: public-repo GitHub Pages and Actions. |
| **Minimum release total** | **$0–$5/month**, plus Kalshi licence terms if pursued. |

## 9. Missing information and genuine blockers

1. **No live samples verified (M1 incomplete).**
   - This session could not run the retrievals. The command-safety check failed
     repeatedly, and web fetches did not use the newly allowed hosts.
   - Required next steps, which are read-only:
     - (a) `GET /historical/cutoff` and `GET /markets?series_ticker=KXNCAAFGAME`
       from Kalshi;
     - (b) one settled game's candlesticks and trades;
     - (c) CFBD `/lines?year=2016…2025` for a handful of known games, checked by
       hand against the archive.

   The CFBD key exists only as a GitHub secret, so CFBD samples should be pulled
   by a manual Actions workflow on this branch or with a locally provided key.
2. **Kalshi display permission (blocker for Market Watch).** Needs written consent
   from Kalshi. Without it, Kalshi data cannot appear publicly.
3. **CFBD redistribution clause.** Read the full terms and confirm that derived
   lines and ATS records may be published. Ask CFBD if the wording is ambiguous.
4. **CFBD per-season line coverage and opening-line availability.** Must be
   measured from real data.
5. **Validation of the spread-to-probability scale** before any probability
   comparison is shown.
6. **The Odds API NCAAF start date and licence.** Unconfirmed; only relevant if
   intraday movement is required.

## 10. Recommended minimum complete V7 feature set

| Feature | Data | Decision |
| --- | --- | --- |
| Team Market History: ATS overall and by season, home/away, favourite/underdog, last 5/10/20, O/U records, cover margin, pushes, coverage denominators | CFBD closing lines plus our results | **GO, conditional** on the sample and redistribution checks (#1, #3) |
| Game detail: model projected margin vs. consensus closing or current spread; model win probability vs. spread-implied probability (validated scale) | Existing model plus CFBD | **GO, conditional** (#1, #5) |
| Opening-to-closing line movement | CFBD opening fields | **Conditional** on measured coverage (#4). Show N/A where missing. |
| Honest validation: 2026 authentic ledger vs. closing lines; 2016–2025 labelled retrospective replay vs. closing lines | Existing archive plus CFBD | **GO, conditional** (#1) |
| Learn & Research explainers: spread, ATS, push, totals, implied probability, bid/ask, liquidity, fees, uncertainty | None | **GO** |
| Market Watch with Kalshi prices, volume, open interest, bid-ask spread and history | Kalshi | **NO-GO until written permission** (#2). If granted: snapshot-based, 2025 onward. |
| Intraday sportsbook movement charts | The Odds API (paid) | **Defer.** Not needed for the minimum release. |
| Model-vs-total comparisons | — | **UNAVAILABLE.** No model total exists. |
| Historical order-book depth | — | **UNAVAILABLE.** |

**Readiness for Milestone 2:** not yet. Proceed when:
- (a) the read-only samples in #1 are retrieved and hand-verified; and
- (b) the CFBD redistribution check (#3) passes.

Kalshi permission (#2) gates only Market Watch. It does not block starting the
CFBD-based historical archive.
