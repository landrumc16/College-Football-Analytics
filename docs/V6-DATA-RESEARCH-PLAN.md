# V6 Data and Research Contract

## Reuse before acquisition
Start with research/archive/verified, V5-HISTORICAL-EVIDENCE.md, genuine pregame forecast archive and existing source manifests. Preserve V5 published snapshots; extend via new versioned datasets and deterministic build scripts. Never rewrite verified history to fit new model results.

## Dataset registry
For each candidate source record provider, original URL, collection date, event date, effective/as-of date, licensing and reuse conditions, coverage by season/team, stable identity key, checksum, extraction method, upstream family and known limitations. Distinct mirrors of one upstream provider do not count as independent verification.

## Priority domains
1. Recruiting: season-specific classes, recruiting composite and player/team mappings with contemporaneous snapshots; avoid retrospectively edited ratings masquerading as pregame information.
2. Rosters and transfers: returning production, portal arrivals/departures, experience and eligibility as known at prediction time; record effective dates and uncertainty.
3. Coaching: head coach/coordinator tenure, changes, continuity and role-effective dates; distinguish announced from effective.
4. Existing results, strength, polls and forecast outcomes: reuse independently verified V5 data and provenance.
5. Optional injuries and depth charts: use only where dated, reliably sourced, permitted and sufficiently complete; otherwise exclude.

## Canonical grain and temporal integrity
Store team-season and game-as-of records separately. Resolve FBS/FCS classification per season and school renames/conference moves via versioned crosswalk. Each feature must have source timestamp <= forecast cutoff, with an embargo if publication lag is unknown. Split historical data chronologically and ensure one game does not appear in train and test via alternate IDs. Explicitly exclude or stratify disrupted 2020 season according to V5 rules; disclose every exclusion.

## Quality gates
Schema and type validation; uniqueness; missingness; bounds; source lineage; upstream independence; cutoff leakage checks; deterministic output checks; coverage by season/conference/program; discrepancy quarantine. No silent imputations for missing recruiting or roster values. Maintain a reusable cache and update only new data or changed sources.

## Publication
Each metric exposes sample size, coverage, as-of time, source attribution and unavailable state. Causal claims require suitable evidence; observational drivers should be labeled associations. Preserve research-only artifacts separately from publishable verified datasets.

## M1 evidence
Commit a registry/manifest, frozen input hashes, coverage table, transformation script, validation tests and a concise unresolved-gaps report. No external-source acquisition is deemed completed merely because an API responds.
