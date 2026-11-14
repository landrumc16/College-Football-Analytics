# V6 Data and Research Contract

## Reuse before acquisition
Start with research/archive/verified, V5-HISTORICAL-EVIDENCE.md, genuine pregame forecast archive and existing source manifests. Preserve V5 published snapshots; extend via new versioned datasets and deterministic build scripts. Never rewrite verified history to fit new model results.

## Audited starting point (planning review, November 14, 2026)

The verified archive contains 1,308 accepted team-seasons out of 1,310,
7,557 corroborated exact FBS–FBS scores out of 7,560, and 40 poll snapshots
(1,000 ranked placements). Keep the exceptions in `comparison.json`; do not
relabel every archived field or FBS–FCS score as independently verified.
The authentic published forecast cohort is 65 2026 Weeks 10–11 games, not four
seasons. Counts describe the retained V5 evidence, not future V6 coverage.

Reuse `talent.py`, `coaching.py`, the `v34_recruiting_*` ingestion/evaluation
modules, staff-continuity validators, `forecast_ledger.py`, and the verified
archive scripts. These validators are infrastructure, not evidence that all
required domain datasets already exist. In particular,
`web/public/v34-recruiting-research.json` has 1,309 joined team-seasons but
`historical_asof_verified: false`: it remains descriptive research and cannot
enter pregame evaluation merely because recruiting class years are known.

## Dataset registry
For each candidate source record provider, original URL, collection date, event date, effective/as-of date, licensing and reuse conditions, coverage by season/team, stable identity key, checksum, extraction method, upstream family and known limitations. Distinct mirrors of one upstream provider do not count as independent verification.

## Priority domains
1. Recruiting: season-specific classes, recruiting composite and player/team mappings with contemporaneous snapshots; avoid retrospectively edited ratings masquerading as pregame information.
2. Rosters and transfers: returning production, portal arrivals/departures, experience and eligibility as known at prediction time; record effective dates and uncertainty.
3. Coaching: head coach/coordinator tenure, changes, continuity and role-effective dates; distinguish announced from effective.
4. Existing results, strength, polls and forecast outcomes: reuse independently verified V5 data and provenance.
5. Optional injuries and depth charts: use only where dated, reliably sourced, permitted and sufficiently complete; otherwise exclude.

## Canonical grain and temporal integrity
Store team-season and game-as-of records separately. Resolve FBS/FCS classification per season and school renames/conference moves via versioned crosswalk. Pregame features require timezone-aware `published_at < forecast_cutoff < kickoff`, `observed_at <= published_at`, and any effective date <= cutoff, matching the existing talent/coaching validators. A later retrieval is usable only when retained evidence establishes the original pre-cutoff publication; a season label or collection timestamp alone is insufficient. Apply a documented embargo when a known publication lag warrants it; exclude unknown availability from pregame use rather than inventing a timestamp. Split historical data chronologically and ensure one game does not appear in train and test via alternate IDs. Explicitly exclude or stratify disrupted 2020 season according to V5 rules; disclose every exclusion.

## Quality gates
Schema and type validation; uniqueness; missingness; bounds; source lineage; upstream independence; cutoff leakage checks; deterministic output checks; coverage by season/conference/program; discrepancy quarantine. No silent imputations for missing recruiting or roster values. Maintain a reusable cache and update only new data or changed sources.

## Publication
Each metric exposes sample size, coverage, as-of time, source attribution and unavailable state. Causal claims require suitable evidence; observational drivers should be labeled associations. Preserve research-only artifacts separately from publishable verified datasets.

## M1 evidence
Commit a registry/manifest, frozen input hashes, coverage table, transformation script, validation tests and a concise unresolved-gaps report. No external-source acquisition is deemed completed merely because an API responds. Each required domain (recruiting, coaching, roster/continuity) must contribute actual usable, sourced observations with declared coverage; an empty registry or unavailable label alone does not complete M1. Missing optional fields may remain unavailable. Loss of an entire required capability needs an explicit owner scope decision; do not block all independent work while resolving access.
