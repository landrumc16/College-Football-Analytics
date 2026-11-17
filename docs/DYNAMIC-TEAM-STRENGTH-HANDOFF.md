# Dynamic Team Strength — research and implementation handoff (2026-11-17)

Status: owner-authorized investigation; **not** a production model change. Branch: `research/dynamic-team-strength`. Do not merge without owner approval.

## Objective
Estimate each FBS team's **current** offensive and defensive strength for upcoming projected scores, margins, win probabilities and downstream projections, without overweighting September results or a single recent game.

## Owner's non-negotiable recency rule
Evaluate a rolling tiered scheme in which the **three most recently completed games each have exactly equal individual weight**. Earlier games can have lower weights in one or more tiers. The illustrative ten-game partition is games 1–4 (oldest), 5–7 (middle), 8–10 (latest, equal). These are *not* prescribed percentages. Roll the window forward after each game; define behavior for 0–9 games, bye weeks and postseason. Compare to the incumbent and alternatives; do not force a promotion if evidence fails.

## Major-change case study
Verify Texas Tech's 2026 starting-quarterback transition involving Tommy Castellanos using pregame-available data. Check whether the incumbent projections actually lagged, and whether any shift is explained by opponent-adjusted recent form. Do not assume a change or grant an arbitrary QB bonus; avoid double counting.

## Repository contracts already inspected
- `AGENTS.md`: inspect existing code and tests first, surgical changes, no unverified claims, preserve production and obtain explicit merge approval.
- `docs/V6-MODEL-EVALUATION.md`: incumbent remains authoritative; distinguish genuine archived pregame forecasts from retrospective replays. Historical 2026 priors must **not** be used to replay 2016–2025. Promotion requires four predeclared eligible held-out seasons; >=5% pooled Brier improvement, gains in >=3/4 seasons, <=2% pooled log-loss regression, favorable 95% clustered interval, no leakage, and acceptable predeclared calibration/coverage. If evidence is missing, research-only; no promotion.
- `docs/V7-ROADMAP.md`: preserve fan-first UI, existing model outputs and market calculator; no invented spreads or forecasts.

## Execution sequence
1. Trace the exact current model and pipeline: game-by-game team ratings, projected points/margin, opponent adjustment, priors, data freshness, score artifacts and downstream UI consumers. Freeze current main SHA and baseline forecast/input snapshot.
2. Identify whether recent games already receive weighting, and whether stale data rather than model design causes any Texas Tech lag.
3. Implement a **research-only** deterministic replay of rolling tier weights using the existing architecture, preferably opponent-adjusted offense and defense rather than raw final scores. Keep three latest games equally weighted in every candidate tiered model.
4. Validate chronological pre-kickoff feature cutoffs, games/season denominators, opponent-strength information availability and baseline parity. Compare spread/score MAE, winner accuracy, Brier, log loss, calibration and targeted major-change cohorts. Report confidence intervals and subgroup tradeoffs; no invented historical market lines.
5. If and only if all applicable promotion gates pass, prepare a minimal implementation, reproducible tests, regenerated current projections and focused PR **without merging**. Otherwise preserve incumbent and document evidence gaps.

## Handoff to Claude Code
Resume from `research/dynamic-team-strength` and this file. Do not search other Claude sessions for the assignment. Check actual GitHub state and existing work before writing code. Report tested SHA, precise tests run, data cutoff, findings and remaining blockers. The current file records scope and repository-contract review, **not** a completed backtest, correction or deployment.

## Verified code trace — 2026-11-17
Inspected current `src/cfb_analytics/ratings.py`, `pipeline.py`, `model.py` and `predictions.py`:
- `calculate_ratings` sums each completed game's opponent-adjusted capped margin with **unit weight**, and uses raw completed-game counts in its ridge denominator. There is no within-season recency weighting in this rating calculation.
- The rating uses eight iterative opponent-adjustment passes, a prior/ridge term, conference shrinkage and a pass chosen from total completed game count. A weighted challenger must preserve coherent scaling of the ridge and conference terms and avoid double-counting.
- `build_season_report` passes `adaptive_rating` to `project_season`, `predict`, rankings and `simulate_cfp`. Any validated rating change therefore affects all those outputs. `predict` maps rating gap plus home advantage to margin and probability.
- The current output stores `home_margin` and `home_win_probability`, **not a separately verified pair of projected team scores**. Do not claim this change updates independently modeled scores unless such a component is identified and validated.
- Current game object includes `week` but no exact kickoff time. For chronological rolling weights, verify deterministic ordering from snapshot start dates and completed status; same-week ordering and late corrections matter.

## Research implementation committed
- `src/cfb_analytics/recency_research.py`: isolated normalized rolling three-tier weight helper, latest three equal.
- `tests/test_recency_research.py`: intended unit coverage for equal weights, short seasons, bye weeks and invalid parameters.
- These files **do not modify production ratings or forecasts**.
- Tests have **not yet been executed in the repository environment**. Do not mark them passing until actually run.
- Latest branch commit at this stage: `e3ccdfe1e9d51dac408a919ce89fb70dd920338c`.
- Next: run tests, inspect current snapshot ordering and available season-specific pregame archives, then implement paired research-only rating replay. No promotion without the V6 evaluation gates.

## Second development pass — research-only challenger
- Added `src/cfb_analytics/recency_rating_research.py`, implementing opponent-adjusted iterative ratings with per-team tier weights and ridge scale preserved by rescaling normalized weights to each team's game count. No production pipeline imports this module.
- Added `tests/test_recency_rating_research.py`, testing exact incumbent parity when all tier weights are 1, a change in ratings with nonunit weights, and invalid-game rejection.
- Latest branch commit: `df2f3a1f447474abb02caeb5cc3ba217cac3dfc3`.
- **Test execution blocked:** attempted to clone the branch into the local execution container, but the container could not resolve `github.com` (DNS). Tests are committed but unverified; GitHub CI or a connected execution environment must run them.
- **Chronology warning:** `ingestion.normalize_cfbd_games` currently sorts by `(week, game_id)`, while `IngestedGame` includes `start_date`. Before replay, establish chronological ordering using valid kickoff timestamps and conservative completed-game cutoffs. Do not mistake `game_id` for kickoff ordering. Preserve incumbent pipeline untouched.
- Next highest-value step: build an as-of chronological replay using verified 2026 inputs; run baseline-parity and leakage tests; compare paired pregame predictions. Do not use current full-season results for past-week features.

## Owner amendment — player availability is secondary (2026-11-17)
Owner decision: prioritize **verified recent team performance** over speculative player-level production losses. Do not assume an unknown backup is substantially worse; Texas Tech's quarterback transition is the motivating example. The latest three completed games remain equally weighted within the rolling current-form tier. Preserve opponent adjustment and earlier-game stability.

Research design constraints:
1. Default to the team-performance model with **no discretionary player-specific point penalty**. A verified absence may justify only a **small, empirically calibrated** adjustment if independent pregame-available evidence supports predictive improvement. No hard-coded universal QB/injury deduction.
2. Never project a backup's unobserved production as if it were known. Distinguish *availability known* from *replacement performance unknown*; surface uncertainty rather than fabricated certainty.
3. Prevent double counting: once post-change games enter the recent-form window, any independent availability adjustment should shrink or expire unless held-out evidence proves incremental value.
4. Compare three paired, leakage-safe ablations: incumbent; rolling team form alone; rolling team form plus modest verified availability signal. Require a measurable incremental improvement for the third before adopting it.
5. Handle major injuries and returns symmetrically in research; report sparse-data and missing-status limitations. Preserve current production until all established promotion gates and explicit owner approval are satisfied.

This amendment supersedes any earlier suggestion to give major roster changes large automatic rating or spread adjustments. No code change is needed solely to record this research priority.

## Owner amendment — Lineup Change Advisory (2026-11-17)
When a verified significant injury, replacement, or return at a key position creates a material unknown about team performance, **display a concise user-facing uncertainty advisory**, rather than imposing a speculative spread/score penalty. The published forecast remains available; say it *may be less reliable* while the new lineup's track record is limited, not that the numbers are known to be inaccurate.

Proposed behavior, subject to evidence and normal review:
- Trigger only from a verified, timestamped source (position, effective game/date, change type, source and last-checked time). No inferred or invented injuries, starters, statuses or performance claims.
- Show the advisory in the matchup/prediction's primary home, and optionally link to it from other surfaces; avoid duplicated full warnings across pages. Make it accessible and understandable to ordinary fans.
- Track completed games *with the changed lineup*, not elapsed weeks or total team games. A provisional three-game observation window is a design hypothesis, **not** a guaranteed clearance threshold; reassess sooner/later according to data availability and whether the same starter actually played.
- Use plain-language copy such as: "Recent starting-quarterback change. The forecast may be less reliable until more games show how the current lineup performs." Distinguish verified fact from model uncertainty. If a status is unverified or stale, do not assert it.
- The recency-weighted model remains driven by opponent-adjusted actual performance; no automatic player-based points deduction. Avoid double counting. An advisory is metadata/communication, not an independent prediction engine.
- Prefer a small maintainable event record and explicit no-advisory state; avoid live scraping, speculative detection, or a broad roster-management system without reliable feeds.
- Validate source/provenance, alert expiry and behavior for replacement reversals, byes, injured player returns, and repeated changes. Test that advisory never silently alters model outputs.

No production change authorized by this documentation. Implement only as part of the focused, owner-approved prediction-accuracy work, with tests and PR review before merge.

## Third development pass — advisory prototype (2026-11-17)
- Added `src/cfb_analytics/lineup_advisory_research.py`: research-only `LineupChange`, `LineupAdvisory`, and `lineup_advisory` with timestamp/source gating, current-lineup confirmation, provisional game-count expiry, and no forecast adjustment.
- Added `tests/test_lineup_advisory_research.py`: tests for advisory wording, provisional expiry, future/unconfirmed changes, and invalid source/timestamp.
- Latest branch commit before this handoff update: `ade4caa307e543b5b0398968372b64b60b970c02`.
- **Not integrated into UI, data feed, or production. Tests not executed.** A source URL format check does not independently verify source credibility. No verified Texas Tech player event has been ingested.
- Next: run unit tests in CI, determine verified event-source workflow and actual starter-participation data, then integrate a single concise accessible advisory into the matchup's primary UI location behind a tested data contract. Avoid repeated banners across pages.

## Fourth development pass — paired chronological replay (2026-11-17)
- Added `src/cfb_analytics/recency_replay_research.py` to generate *retrospective* paired incumbent/challenger pregame estimates. Each target game uses only earlier kickoffs whose conservative kickoff-plus-four-hour result window precedes target kickoff. This is not a substitute for verified actual result publication timestamps.
- Added `tests/test_recency_replay_research.py` for same-day cutoff, input-order independence, paired metrics, duplicate IDs, and missing kickoff.
- Latest implementation commit: `25d2f7b4e9919797f5be5c86b77be923195010b9`.
- Important: **No real historical replay metrics have been produced**, and none of the new tests have yet been executed. Season-specific historically available priors and source publication provenance must be verified before making historical accuracy claims. Do not mistake a replay for a published archived forecast.
- Next finish-first work: execute tests in GitHub Actions or another actual runtime; use a verified season-specific dataset to produce paired scorecard; fix any failures; wire a single accessible UI advisory to a source-verified event feed; keep draft PR #38 unmerged.
