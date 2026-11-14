# V6 Prediction Research and Challenger Promotion Standard

## Baseline
Keep the released V5 incumbent prediction engine as production authority. Freeze its code SHA, input snapshot, forecast archive and evaluation methodology. Distinguish authentic archived pregame predictions from retrospective replays; never report replay accuracy as historical live accuracy.

## Two distinct evidence lanes

1. **Authentic published forecasts:** reproduce the retained 65-game 2026
   Weeks 10–11 cohort with `v5_forecast_evaluation.py` and
   `scripts/verify_v5_pregame_archive.py`, then append genuinely timestamped
   future forecasts through the existing ledger. Freeze the original cohort and
   report new cohorts separately. Do not imply four archived seasons exist.
2. **Out-of-time retrospective research:** freeze and replay the incumbent and
   challenger on identical chronological game cohorts using only independently
   evidenced pre-cutoff inputs. This can supply multi-season paired research,
   but must be labelled a retrospective replay, never authentic historical live
   forecasts. An archived incumbent forecast must not be silently compared with
   a recomputed challenger on a different feature cutoff or game sample.

The current `pipeline.py` explicitly uses frozen 2026 workbook priors and
conference membership until a season-specific feed exists. Freezing that code
alone does not make its inputs valid for 2016–2025. A true incumbent replay
requires season-specific pre-cutoff priors, roster/classification/conferences
and rolling ratings as well as time-safe challenger features. Never seed an
older season with 2026 ratings or later final standings. If those incumbent
inputs cannot be established, label any alternative a proxy/reference baseline;
it cannot satisfy the incumbent-paired promotion gate.

## Evaluation design
Use rolling chronological, season-held-out validation. Predeclare exactly four distinct primary held-out seasons with genuinely pregame-available inputs for the existing four-fold promotion gate; report any additional seasons too and never select the best four after observing results. If four eligible seasons cannot be established, report research-only results and defer promotion. Evaluate the same eligible games for both models. No training on outcomes or rankings published after each kickoff. Record feature availability, cutoff, training windows, hyperparameter selection and random seeds. Cluster uncertainty by game/week or season as justified, and avoid treating correlated simulations as independent observations.

Reuse `v4_evaluation.evaluate_pairs`, `clustered_brier_interval` and
`assess_release_gates` for paired replay research. The numerical gate helper
accepts retrospective rows and exactly four seasons; it does not prove source
authenticity or authorize deployment. The older two-season/100-game
`v34_promotion.promotion_gate` cannot substitute for V6's stricter gates.
Default uncertainty uses the existing paired (season, week) cluster bootstrap
with 2,000 draws and seed 2026; freeze any justified alternative before testing.

## Required metrics
Pooled Brier score and relative improvement; log loss; winner accuracy with denominators; reliability/calibration curves and error; coverage and abstention rates; baseline comparisons; season and conference breakdowns; uncertainty interval for paired score differences. Avoid optimizing accuracy alone at the expense of calibration.

## Mandatory promotion gates (carry forward V5 standard)
- At least 5% pooled Brier improvement on identical held-out games.
- Improvement in at least 3 of 4 held-out seasons.
- No more than 2% regression in pooled log loss.
- Favorable 95% clustered confidence interval: the upper bound for challenger-minus-incumbent mean Brier is strictly below zero.
- No leakage; acceptable calibration and coverage, with explicit predeclared tolerances.
All gates are conjunctive. During the incumbent-baseline phase, freeze an evaluation protocol with the four seasons, game eligibility/denominator, minimum sample sizes, calibration metric/bins and numeric tolerance, coverage/abstention floors, uncertainty method, seeds and training/tuning windows before any challenger tuning or held-out inspection. These are mandatory recorded prerequisites, not unspecified gates that can be marked passed; unset tolerances or insufficient coverage mean not promotion-eligible. They cannot relax the fixed Brier/log-loss/season/interval requirements. No cherry-picked seasons, altered gates or selective test exclusions.

## Decision
If all gates pass, submit exact frozen evidence and seek **separate explicit owner approval** before promotion. Otherwise incumbent remains in production; challenger can remain isolated in Research. Explain what was learned without claiming a production improvement. Matchup explanations must derive from real features/attributions, not generated narratives unsupported by the model.

## Evidence package
Machine-readable predictions and outcomes; provenance and cutoffs; evaluation script and tests; frozen model/input SHAs; reproducible metrics; paired uncertainty method; failure and subgroup analysis; promotion recommendation and approval status.
