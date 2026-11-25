# V9 execution state — November 25, 2026

## Baseline and authority

Main inspected at 13fb09a924e7906aa6db474fc291a8544e1da3a0. Authenticated GitHub identity landrumc16 has admin permission. Full local clone, Python/Node dependencies and build environment work. AGENTS.md read in full. Open PRs are 56 (active freshness fix), 37 (research), 35 (release guard cleanup), 32 (older market plan). Their branches were not modified.

## Owner feedback and reuse

The owner rejected cheap/minimal/crowded standalone HTML previews. Use the actual application and existing components for all previews. Research/product-definition artifacts informed docs/V9-ROADMAP.md. Reuse EditorialHome.tsx, TeamProfile.tsx, OffenseDefense.tsx, ModelProjections.tsx, strengthScores.ts, v8_stats.py, forecast_ledger.py and existing archives. Published model rank combines projected wins and rating and must not be relabeled rating-only strength rank.

## Completed pass

- Isolated v9-development from the inspected main baseline.
- Definitive three-milestone roadmap.
- Offline immutable strength-report observation command scripts/v9_strength_snapshot.py. Example invocation uses --report data/season-2026-report.json --archive an isolated archive directory --source-commit the exact baseline SHA.
- Source SHA256, exact source commit, source receipt, report generation time and retention time are retained separately. Snapshot records are retained observations, not proof of original public availability.
- Atomic complete-file publication through same-filesystem hard link and idempotent retries.

## Actual verification

- Baseline python -m pytest -q: 820 passed, 2 skipped.
- New snapshot tests: 2 passed.
- npm run build in web: successful TypeScript and Vite build.
- Offline command against real report: successful, 138 teams.
- Frontend output unchanged by this pass. No API calls or workflow dispatches.

## Outstanding

No UI integration, source-contract registry, new accomplishment metric, publication-pipeline integration or historic backfill is complete. No five-width browser, visual baseline, PWA or physical-device evidence was collected in this pass. A normal Android-accessible isolated preview remains to be established using the actual web build. Prior session's cloud browser could not access local preview and rejected embedded URLs. Use an authorized actual-app preview host rather than another standalone prototype or any security-policy workaround.

Next pass should validate snapshot schema and corruption behavior more fully, integrate retention into an isolated offline build path, then implement the shared intelligence contract using existing functions. Keep actual publication time unknown unless independently evidenced. Reconcile PR56 only after its independent merge. Inspect protected-change guards before any protected path edit. Run targeted tests and relevant regression checks. Publish preview separately from production with analytics disabled. Do not treat retained report observation as historical pregame forecast evidence.

No owner decision blocks these routine steps. New accomplishment rankings, engine promotion and quantified rooting retain their validation gates. V9 merging requires explicit owner approval.

## Foundation publication pass

Added scripts/v9_intelligence.mjs. It bundles and calls the actual released strengthScores.ts, packages all 138 teams, retained record accomplishment, season strength, current three-game level, V8 adjusted units, four-game-requested trends with actual fallback window, schedule context, consistency and source metadata. New accomplishment national metric remains null. Retained snapshot history is integrated into an isolated offline publisher.

Added V9-only read-only-permission artifact workflow. It uses committed source files and no CFBD requests, schedules, Pages deployment or production secrets. It publishes the retained observation and shared intelligence JSON as an artifact. Workflow execution is not yet verified.

Verification: full Python suite 823 passed, 2 skipped. Targeted publication test passes with identical Official report and dual-projection hashes before/after and exact season-rating equality across 138 teams. Contract cases pass for missing stats, thin sample, duplicate teams and nonfinite rating. TypeScript/Vite build passes, same generated frontend asset names as baseline. No new forecast model or statistical improvement claim.

Acceptance remaining: source-age assessment is explicitly delegated to the consumer and lacks tested stale/future-time classification. Findings currently contain the season-strength statement with traceable evidence, while richer unit/schedule/current-level explanation rules remain to implement. Schema validation is partial, including consistency sample metadata. Thus Milestone 1 is not closed. These are engineering tasks, not an environment blocker. Continue them before Milestone 2 integration. Browser baselines remain unavailable in this pass and prior environment browser restrictions still apply. No actual-app external preview has been established.

Next targeted pass: complete field-level period/sample/uncertainty contracts, validate missing/future/stale timestamps, generate supported unit/current/schedule findings and test contradiction/rounding behavior. Add TypeScript consumer contract, independent all-team parity against existing unit fixture and archive corruption/schema tests. Verify isolated workflow artifact without touching production. Milestone acceptance requires those outcomes, not merely the new publisher.

## Milestone 1 acceptance — final foundation pass

Completed shared metric/finding contracts including a TypeScript consumer contract. Metric wrappers retain units, population, sample, period, source receipt, limitations and availability. Source-age classification tests cover missing, invalid, timezone-less, future, stale and current timestamps. The 24-hour default is an explicit configurable descriptive age threshold, not a claim of achieved event-driven freshness.

Added deterministic earned-record, current-level, adjusted-unit and schedule findings. Evidence paths resolve across all 138 published teams. Missing unit values suppress unit findings. Period-specific wording avoids a season/recent contradiction. No inferred personnel or causal claims. Existing production strength function is bundled directly. Four-game trend metadata preserves actual three-game fallback. Accomplishment remains actual earned record; unvalidated national metric stays unavailable.

Durable initial report observation retained in docs/evidence/v9/strength-history. Each future V9-only publication restores the retained history, archives the current report and commits new observations only to v9-development. Source bytes identify the observation. Repeated source bytes preserve the first retention/source commit. Tampered stored team values are rejected. Publication time stays unknown. Artifact retention alone is not relied upon for permanent history.

Snapshot and team-intelligence publication both ran successfully offline. Final targeted Python tests passed (4). Node missing-data/freshness/evidence cases passed. Full suite passed 824 with 2 skipped before the final retention wiring adjustment; targeted publication/archive tests reran after that adjustment. TypeScript/Vite build passed with unchanged frontend asset names. Official and dual source-artifact hashes preserved in publication regression tests. All-team season ratings equal source report values exactly. No predictive improvement or new statistical inference is claimed.

Milestone 1 data-foundation acceptance is satisfied locally. Remote workflow execution remains to be observed after commit. Browser visual baselines remain unavailable, with no new browser/physical-device pass claimed. The UI is unchanged. Milestone 2 may begin with the existing components while remote CI and preview-environment checks remain explicit release gates. No production workflows were dispatched or production API calls made.
