# V9 Final Release Preparation — November 26, 2026

## Decision and Exact State

The owner explicitly approved PR #56 at its verified head. It merged as `79a3b1bf42236a852caf11b15c78b12b5a636a7e`. V9 is reconciled with that main revision. PR #63 still requires separate explicit owner approval; do not merge or deploy it automatically.

- PR #56: `edc9598aab01b625ad68144e93feea9f999a3a61`, open, mergeable, 11 successful checks and one expected skip at inspection.
- PR #63 input head: `52c477e8d19e23f4008ef68b68f85bd6669ae5e1`, open, mergeable; only failing check was the stale JavaScript baseline.
- Current production/main source: `b204bd6f38629540d45bfb4a885b20909b7f2c0b`.
- The exact preparation candidate is the commit containing this document. Its CI must be inspected; a local pass is not a remote CI claim.

PR #56 preserves independently observable quota/watcher warnings across alternating monitor passes and redeploys only when critical alert keys change. Its four-file scope is the monitor, exact protected-change manifest and regression/guard tests. It changes no prediction calculation. The 40 targeted reliability/guard tests pass locally. Existing GitHub checks are green. It is ready for explicit owner merge approval.

## Option C — Authorized Budget Correction

The old baseline was November 17 production `474c72d`. Pin the same comparison to current production `b204bd6`, with identical environment/dependencies for both builds. Keep the **10,240-byte** growth allowance, assertion, original protected paths, exact-release manifest checks, fork rejection, privacy tests, browser journeys and failure evidence retention unchanged.

Independent Node 24 builds: production **115,358 bytes**, V9 **123,076 bytes**, growth **7,718 bytes**, remaining allowance **2,522 bytes**, all gzip JavaScript including worker chunks. CI uses Node 20 and will independently measure both sides. See `evidence/v9/production-js-baseline-2026-11-26.json`. Live production entry-script retrieval succeeded; its configuration and exclusion of worker chunks make it unsuitable as the like-for-like budget total. No production API quota was consumed.

## Acceptance Reused and Validation Executed

Claude's `V9-INDEPENDENT-ACCEPTANCE.md` and `V9-DEVICE-TESTING.md` remain authoritative for completed browser and automated-device acceptance. Do not repeat their research/design/device passes. All three milestones are implemented; approved React design, five-width journeys, exact scenario/reset behavior, Title Case, accessibility review, performance and Chromium PWA lifecycle were verified there. Physical hardware was not tested; WebKit offline/update remains limited by its recorded Linux crash. The owner accepted those limitations; neither requires owner manual testing.

This pass: TypeScript/Vite builds pass for production and candidate. Full V9 Python regression with `REQUIRE_WEB_BUILD=1`: **838 passed, 1 skipped**. Unit suites pass: strength 8 cases (Python/TypeScript parity across 138 teams), V8 stats 6, model projection explanations 7, prediction explanations 7, freshness 7. Current Official margins reproduce across 71 games. `git diff b204bd6 -- src/cfb_analytics` is empty: production model source is byte-identical. This pass edits no UI, data, prediction formula or refresh schedule.

## Required Release Sequence

1. Obtain owner approval for PR #56 at the exact head above; recheck head and checks immediately before merging. Record merge SHA, successful Pages deployment, live data/scenario identity and freshness-monitor behavior. Do not induce warnings or call paid data APIs to test.
2. Fetch actual main after that authorized release. Merge it into `v9-development`; preserve all reliability changes. Resolve only genuine conflicts. If the guard-test manifest list conflicts, retain all reviewed branches and negative tests, including `freshness-alert-flapping`, `freshness-reliability`, `v7-development`, `v9-development`.
3. Keep the b204bd6 budget reference if frontend source is unchanged by the hotfix; otherwise measure actual production and explicitly reconcile the pinned baseline. Never increase the allowance to clear a failure.
4. Run full Python, TypeScript/build, protected/negative guards and every applicable PR CI workflow on the reconciled exact head. Reuse prior visual acceptance when UI remains unchanged. Inspect privacy/browser size artifact and device checks; account for expected skips. Recheck source/paired data, immutable archive receipts, forecasts and source freshness.
5. Publish the exact reconciled head, all check results and any remaining blockers for **separate V9 owner approval**. The present pre-hotfix preparation head is not the final post-reconciliation release candidate.
6. Only after authorization, merge V9 and verify the normal main deployment. Do not manually trigger acquisition, deploy previews to production, alter watchers or bypass safeguards.

## Production Verification and Rollback

Before promotion, record the successful post-PR56 production SHA, deployment/run ID and retrievable known-good Pages artifact; this is the rollback target, preserving the reliability fix. Record current valid data and immutable prediction/strength archive hashes.

After authorized V9 deployment, verify all five destinations, search, favorites persistence, chart disclosures, predictions/model labels, research denominators, scenario override/exact reset, paired scenario/report hashes, unavailable-data behavior and visible source timestamps. Confirm normal event-driven scores/polls and the independent monitor/watchers remain healthy. Verify service-worker update, offline shell and online recovery in automated Chromium; do not claim physical hardware verification. Confirm no private data or credentials are staged. Record deployment SHA and results.

If critical acceptance fails, halt release sign-off. Prefer restoration of the retained known-good Pages artifact through the approved deployment process if available. Otherwise prepare a targeted rollback PR reverting V9 code/workflow changes while preserving PR56, newest valid data and immutable archives. Obtain explicit owner approval before merging/deploying rollback. Never force-reset main, erase issued predictions/history or revert independent reliability work. Record incident cause, rollback SHA, deployment and restored checks.

## Outstanding Gates

- Confirm successful PR #56 production run `45885177456` and retain its live verification evidence.
- Inspect all final exact-head CI results for the reconciled candidate.
- Final V9 approval, then authorized deployment and live verification.

No new feature, model promotion, quantified rooting guide, accomplishment ranking, redesign or subscription is included. Existing small-sample dual-model accountability limitations remain honestly unavailable until authentic games settle. Previous private preview and completed automated-device evidence remain valid for the unchanged approved interface.

## Post-Hotfix Reconciliation

PR #56 head and 11 successful/one expected skipped checks were reconfirmed before the SHA-guarded authorized merge. Its production run is https://github.com/landrumc16/College-Football-Analytics/actions/runs/45885177456. Current production data and the exact monitor change are integrated. The sole conflict in tests/test_protected_guard.py retains all four reviewed manifest branches and both sets of negative tests. No frontend or device-test files changed from approved head fac98f8. All src files are byte-identical to post-hotfix main.

Reconciled full Python regression with REQUIRE_WEB_BUILD=1: **839 passed, 2 skipped**, 26.78 seconds. The real offline React review build passes, including paired report/scenario and V9 packets. The first pre-commit test attempt correctly rejected the monitor because the guard hashes committed HEAD; rerunning against the committed merge passes without weakening the guard. Exact final remote CI results and live hotfix verification must be checked before owner release approval; this document does not predeclare those asynchronous results. Prior browser/device acceptance is reused for unchanged UI, alongside automatically triggered CI.
