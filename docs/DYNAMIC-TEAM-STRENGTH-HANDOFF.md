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
