# V6 implementation evidence

This records delivered evidence under the approved roadmap; it is not another
roadmap. Exact tested commits and workflow links are recorded in the V6 PR.

## M1 — verified research foundation

Implemented 2016–2026 derived observations for 1,452 NCAA-classified team-seasons:
1,449 recruiting, 1,449 roster and 1,450 coaching records. Current 2026 coverage
is 138/138 programs in each domain. Independent NCAA classification includes
transition/opt-out programs, so the denominator differs from played-game cohorts.
Missing domains: Coastal Carolina 2016; Liberty coaching 2017; Old Dominion and
UConn recruiting/rosters 2020. Missing records and optional coordinator/effective-
date/injury/depth-chart histories remain unavailable, never imputed.

The immutable publisher registry pins 38 original inputs. A 31,446,463-byte
private owner source archive is retained separately, SHA-256
`4dcf061b75a5b67224046c0cdf1b72249130c88f3e9844037f0b6af31acaa541`.
Raw coaching names and athlete biographies are not published to GitHub.
Public derived records, per-season/per-conference coverage, field missingness,
canonical NCAA/ESPN identity links and source hashes support M2/M3 consumers.
Source-name recovery uses unique exact publisher labels, never fuzzy matching.
Unjoined source rows include FCS/uncommitted observations outside the denominator;
those diagnostics do not mean all such records are source errors.

Historical biography experience is excluded to avoid backfills. Recruiting grade
units are retained without capping or treating grades as percentages. Roster
retention measures membership, not returning playing production. Coach continuity
is descriptive dominant-season attribution, not proof of current staff or causality.
The source registry verifies publisher bytes and quality, not every underlying
player fact independently or historical pregame publication times.

Executed: deterministic offline rebuild matched the retained corpus byte-for-byte;
10 new source/identity/temporal/missingness safeguards and the complete 536-test
Python suite passed. The verified V5 archive and incumbent remain unchanged.

## M2 — prediction intelligence

The pre-test protocol is frozen in `research/v6/evaluation-protocol.json` before
challenger fitting or held-out inspection. Four chronological seasons, calibration
and coverage limits, paired scoring/uncertainty and numerical gates are fixed.
Known historical availability and incumbent-prior gaps are declared before results;
proxy research cannot authorize promotion or claim a production accuracy gain.

## M4 — predeclared browser scenario budget (before implementation/benchmark)

Use 2,000 deterministic seeded draws per run in a dedicated worker. A run must
finish within 3,000 ms under Chromium 4× CPU throttling at 390×844, using the
actual current national schedule. Main-thread navigation must remain responsive.
The maximum per-probability Monte Carlo 95% half-width is 2.2 percentage points;
a difference between independent 2,000-draw runs has a worst-case 3.1-point
half-width. Comparisons use common random draws to reduce noise. Seeded reset
must reproduce exactly. Browser/Python reference fixtures must agree within
1e-9 with a shared random source; comparison to the independently seeded
10,000-draw published forecast allows at most 5 percentage points per displayed
probability. Do not describe these conditional simulations as committee forecasts.

## Delivered research and application integration

M1 cross-runtime canonical JSON reproduction passed Python 3.11 CI at
`99ab0bec814ad653ea6a9f14434b8be08c8f03b8`, research run
[43614269903](https://github.com/landrumc16/College-Football-Analytics/actions/runs/43614269903).
Numeric means use accurate summation across Python 3.11/3.12. The retained
compressed file has its own checksum; canonical decompressed JSON is compared
exactly during rebuild so zlib container differences cannot alter acceptance.

M2 preregistration was committed at `04f3ff6b8f548fe43face56f67af04f7f5ed0899`
before fitting/inspection. The 2022/23/24/25 folds contain 766/758/763/772 common
games, 3,059 pooled; coverage is 98.71/95.71/95.61/95.54%. Lagged results and
home location are the only features. The reference is a prior-results logistic
proxy, **not the released incumbent**. Pooled reference/challenger Brier:
0.221772/0.221793; log loss: 0.634014/0.633601; winner accuracy:
63.62%/63.55%. Paired challenger-minus-reference Brier 95% interval:
[-0.001741, +0.001775], 2,000 paired season/week cluster draws, 62 clusters.
No reliable advantage was established; no hyperparameter tuning followed.
Frozen predictions, calibration bins, four folds, conference breakdowns,
missing-history abstentions, hashes and all failed/passed proxy screens are
retained. Historical incumbent priors and original historical cutoff evidence
remain unavailable, so incumbent promotion gates cannot be claimed passed.
Decision: **retain incumbent; experimental research only**.

The separate authentic archive reproduces 65 issued-before-kickoff predictions,
64.62% correct winners, Brier 0.211392, log loss 0.610860. This is two partial
2026 weeks, not four archived seasons. Research UI keeps these lanes separate.
An isolated 178-game experimental future cohort was frozen and independently
published by GitHub artifact 14121407839 at 2026-11-14T16:12:37Z before every
selected kickoff; original model/prediction bytes and receipt are retained.
No prospective score is claimed before independent final-outcome verification.

M3 uses one shared Python transform and one React component across Team Profile
Historical Intelligence, a selected Program Directory school and Compare.
The public packet contains 139 programs with observed FBS history (138 current
2026 programs plus historical Idaho). It describes two completed three-season
windows, recruiting blue-chip composition, observed roster retention and dominant
head-coach continuity; unavailable periods remain unavailable. Exact periods,
counts, source links/hashes, national coverage and non-causal limits are exposed.
2020 is excluded from performance windows. No V5 grades or calculations change.

M4 reuses cfp.py with optional scenario/random adapters; default incumbent draws
are preserved. The static browser worker implements the same conference,
selection and playoff rules. Python/browser outputs match exactly for three
2,000-draw national fixtures (baseline and opposite Army/Navy winners), including
CFP, conference and national-title probabilities. Reset is exact. The maximum
baseline CFP/conference difference versus the published independently seeded
10,000-draw run is 2.09 percentage points, within the predeclared 5-point limit.
Overrides reject unknown identities, wrong participants, duplicate/conflicting
identities, completed games and started/undated choices. A SHA-256 check ties
scenario inputs to the exact current report. National inputs regenerate during
production build; no live API/backend or model replacement is introduced.

M5 retains the five-section homepage, bottom navigation and adaptive section
selectors. Saved-team rows now show next-game week and opponent model rank;
favorites lead scenario results. Detailed matchup probabilities remain incumbent
outputs, with real rating/location context. Unsupported forecast movement is
explicitly unavailable rather than synthesized from a recomputation.

Local verification of this integrated pass: 547 Python regressions passed,
TypeScript/Vite production build passed, three Python/browser algorithm parity
fixtures and published-baseline tolerance passed, and research/product export
reproduction passed. Five-width browser screenshots, throttled runtime and PWA
journeys are required on the final candidate; pending results must not be inferred
from the algorithm checks. No implementation merge or model promotion authorized.
