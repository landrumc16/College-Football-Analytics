# Version 6.0 — released and closed

Version 6 preserves the Version 5 design, navigation, verified archive and
incumbent prediction engine. The owner approved PR #25 after visual review;
production deployment and live acceptance passed. Deployed commit:
`fda1fc284a6214611eeae4451d67daaea722d670`. See [formal production closeout](V6-PRODUCTION-ACCEPTANCE.md).

Live application: https://landrumc16.github.io/College-Football-Analytics/

## Delivered capabilities

- Reusable 2016–2026 recruiting, observed roster continuity and dominant head-coach
  history: 1,452 classified team-seasons, with current 138/138 coverage in each
  domain. Raw source inputs retained privately; derived records, source hashes,
  immutable URLs, missingness and identity links retained publicly.
- Frozen chronological prediction research for 3,059 paired 2022–2025 games;
  separate authentic 65-game incumbent evidence; calibration, uncertainty,
  conference/season breakdowns, coverage and all promotion gates exposed.
- Shared sourced program context in Profiles, Program Directory and Compare:
  recruiting composition, observed roster retention, coaching continuity and
  completed-season performance comparisons, with periods and limitations.
- Static-hosted CFP/conference what-if simulations: future winner selections,
  exact seeded reset, baseline comparison, favorites first, worker computation,
  exact Python reference parity and report-checksum freshness validation.
- Favorite-team rows include next-game week and opponent model rank. Full game
  analysis keeps incumbent probabilities and actual rating/location context.

## Prediction decision

Retain the incumbent. The challenger did not establish a reliable advantage even
against its prior-results reference proxy; that proxy is not the production
incumbent. Brier: reference 0.221772 vs challenger 0.221793; paired 95% interval
[-0.001741, +0.001775]. Historical incumbent priors and original contextual
publication cutoffs are unverified. Promotion is neither eligible nor authorized.
An independently timestamped 178-game experimental future cohort is retained
for later outcome evaluation; no future accuracy is claimed today.

## Limits and operations

Recruiting/roster/coaching records are sourced observations, not independently
corroborated player facts or causal explanations. Historical original publication
times remain unproven, so these contextual fields cannot enter historical pregame
fitting. Historical roster biography experience is excluded. Roster overlap is
membership, not playing production or a verified transfer-only history. Exact
coordinator/effective-date/injury/depth-chart information remains unavailable.
Missing records and incomplete performance windows are not silently filled.

Scenarios retain the incumbent's top-two conference-win/rating tiebreak,
five-champion/seven-at-large and committee approximations. Same-conference games
are inferred from membership; special nonconference games between conference
members are not separately modeled. A scenario is a conditional model estimate,
not an official selection or a new authoritative forecast. 2,000 seeded draws
have a worst-case single-probability 95% half-width of approximately 2.2 points.
The independent published 10,000-draw forecast remains available unchanged.

The deployment build runs `python -m scripts.build_v6_product` so scenario packets
match the current report, without a Python backend. Research exports rebuild
from retained pinned inputs; only the optional research decoder needs PyArrow.
Raw restricted source inputs must never enter public caches or CI artifacts.
The service worker retains live JSON's network-only contract and explicit
offline fallback. Android evidence uses Chromium emulation, not a physical device.

## Acceptance evidence

PR #25 records the exact final tested SHA, workflow URLs, counts, inspected
screenshots, runtime results and any blockers. The preserved V5 browser suite
covers five widths, favorites isolation/persistence, search, polls, predictions,
profiles, historical intelligence and Android PWA install/update/offline/recovery.
V6 adds shared-context parity, truthful research lanes, future-only scenarios,
exact reset, Python parity and the predeclared 4× CPU mobile runtime check.

Screenshot inventory per width (375, 390, 430, 768, 1536): editorial homepage,
Team Profile context, Research and Playoff scenarios, plus existing full-view and
Android PWA screenshots. Final artifacts are attached to the PR acceptance runs.

Owner implementation-merge approval and production acceptance are recorded in the closeout. No challenger promotion was authorized or performed.
