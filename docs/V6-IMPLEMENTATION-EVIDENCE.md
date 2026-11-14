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
