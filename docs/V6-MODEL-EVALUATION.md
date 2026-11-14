# V6 Prediction Research and Challenger Promotion Standard

## Baseline
Keep the released V5 incumbent prediction engine as production authority. Freeze its code SHA, input snapshot, forecast archive and evaluation methodology. Distinguish authentic archived pregame predictions from retrospective replays; never report replay accuracy as historical live accuracy.

## Evaluation design
Use rolling chronological, season-held-out validation. At least four held-out seasons with genuinely pregame-available inputs for the promotion gate; if unavailable, report research-only results and defer promotion. Evaluate the same eligible games for both models. No training on outcomes or rankings published after each kickoff. Record feature availability, cutoff, training windows, hyperparameter selection and random seeds. Cluster uncertainty by game/week or season as justified, and avoid treating correlated simulations as independent observations.

## Required metrics
Pooled Brier score and relative improvement; log loss; winner accuracy with denominators; reliability/calibration curves and error; coverage and abstention rates; baseline comparisons; season and conference breakdowns; uncertainty interval for paired score differences. Avoid optimizing accuracy alone at the expense of calibration.

## Mandatory promotion gates (carry forward V5 standard)
- At least 5% pooled Brier improvement on identical held-out games.
- Improvement in at least 3 of 4 held-out seasons.
- No more than 2% regression in pooled log loss.
- Favorable 95% clustered confidence interval for paired improvement.
- No leakage; acceptable calibration and coverage, with explicit predeclared tolerances.
All gates are conjunctive. Define the calibration and coverage thresholds before challenger testing. No cherry-picked seasons, altered gates or selective test exclusions.

## Decision
If all gates pass, submit exact frozen evidence and seek **separate explicit owner approval** before promotion. Otherwise incumbent remains in production; challenger can remain isolated in Research. Explain what was learned without claiming a production improvement. Matchup explanations must derive from real features/attributions, not generated narratives unsupported by the model.

## Evidence package
Machine-readable predictions and outcomes; provenance and cutoffs; evaluation script and tests; frozen model/input SHAs; reproducible metrics; paired uncertainty method; failure and subgroup analysis; promotion recommendation and approval status.
