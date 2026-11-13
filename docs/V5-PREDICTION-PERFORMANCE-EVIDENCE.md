# V5 authentic prediction-performance evidence — November 13, 2026

The mandatory archived-pregame requirement is satisfied for a bounded, genuine
2026 Weeks 10–11 FBS-versus-FBS cohort. This is not a ten-year forecast archive or
a full-season accuracy claim.

The original ledger is retained from immutable commit
`42aa772a4d8f3d0095865e2a0946ae7e4813a790`, Git blob
`fbaf1d36a81199a278b85a433e5ddbe3a32f9869`. GitHub Actions publication run
[42076089302](https://github.com/landrumc16/College-Football-Analytics/actions/runs/42076089302)
records that commit at server time `2026-11-05T17:35:19Z`, before every scored
kickoff. All 65 forecast entries remain byte-equivalent as parsed records in
the current first-observation ledger; modified forecasts fail verification.
The source retrieval, prediction, server publication and kickoff timestamps
are checked independently of a retrospective model calculation.

All 65 final scores agree with the independent NCAA-origin schedule. The
join requires canonical team identities, scheduled date, a unique NCAA contest,
and identical scores. Five optional ESPN-ID crosswalks are absent or differ;
those provider identifiers are documented rather than silently equated.

| Metric | Reproduced value |
| --- | ---: |
| Scored games | 65 |
| Correct winners | 42 |
| Winner accuracy | 0.6461538462 |
| Brier | 0.2113917032 |
| Log loss | 0.6108603105 |
| Low-confidence games / accuracy | 18 / 50.0% |
| Medium-confidence games / accuracy | 21 / 57.1% |
| High-confidence games / accuracy | 26 / 80.8% |
| Same-game neutral 50/50 Brier | 0.25 |
| Same-game neutral 50/50 log loss | 0.6931471806 |

The existing `v5_forecast_evaluation.py` produces calibration, confidence
segments and paired baseline metrics. Coverage is published with the actual
outcome snapshot date and eligible completed-game denominator; the independently frozen November 13
outcome snapshot contains 570 eligible completed games (65/570 = 11.40%).
This verified cohort remains fixed as later live updates arrive. It does not
silently claim independent review of newly completed games.

In the earlier November 9 Week 10 reconciliation, the preliminary 58th match was Wake Forest–Merrimack, an FCS fixture outside
the declared FBS-versus-FBS scope. Excluding it exactly reproduces the existing
57-game Week 10 scorecard (35 correct). The fresh November 13 report adds eight settled Week 11 games, all independently corroborated, for 65 games and 42 correct overall. Legacy entries without complete pregame provenance, future
fixtures, retrospective walk-forward studies and challenger outputs are excluded.

Retained evidence is in `research/archive/verified/`: original published ledger,
server publication receipt, verified evaluator rows, independent NCAA bytes and
per-game outcome matches. `web/public/v5-forecast-evaluation.json` is integrated
in Research & Data with sample size, scope, as-of date, coverage, confidence
segments and the neutral baseline. The incumbent engine is unchanged.

```bash
PYTHONPATH=src python -m scripts.verify_v5_pregame_archive
python -m pytest -q tests/test_v5_verified_publication.py
```

The original production refresh workflow is never dispatched from development:
it writes to `main`. V5 acceptance exercises provider refresh and report creation
in an isolated checkout, retaining an artifact without publishing to production.
