# Existing rapid-result lifecycle integration

The original V5 reconciler remains the validation/independence authority for secondary
observations. `rapid_results` adds event-specific durable lifecycle state around it;
it makes no provider requests. Unauthorized sources remain disabled.

`rapid_results_cli` takes `--inbox`, `--schedule`, `--sources`, `--state`,
`--output`, and `--archive`. The retained report (or schedule list) supplies exact
canonical game ID and home/away identity. Registry JSON is `{ "enabled": false,
"sources": {} }`; each explicitly authorized source URL maps to a provider kind.
Only the exact CFBD games URL with kind `cfbd` may verify a result. The rapid
inbox cannot assert authority. Inbox JSON is `{ "batch_id": "...",
"observations": [{ "observation": { ... } }] }`.

An observation contains `kind: game_final`, `status: final`, canonical identity,
integer final scores, HTTPS `source`, timezone-aware `published_at` and
`observed_at`. Optional `basic_stats` holds home/away maps of nonnegative integer
total_yards, passing_yards, rushing_yards, turnovers and first_downs. Incomplete
statistics are explicitly pending. Rapid scores can be published separately with
provisional record overlays without changing incumbent prediction inputs.

Later `--cfbd-snapshot` accepts a retained normalized games/schedule snapshot
with a `retrieved_at` receipt, reuses only completed games already in rapid state,
and verifies or corrects their results. `--confirmed-games` optionally exports
verified games for downstream integration. Normal existing CFBD refresh remains
the canonical model recalculation path; no formulas are replaced. CFBD verification
is explicit, not a claim that CFBD and ESPN are independent upstreams.

State includes append-only observation history and processed batch IDs. Advisory
writer locks plus expected revision reject concurrent stale writes; atomic replace
commits state before public export. Identical observation replays are idempotent.
Authoritative evidence exports use immutable content-addressed filenames. Public
export/archive failure can be recovered by replaying the same retained inbox.
These new archives never modify existing historical or pregame forecast archives.

Controlled CLI tests cover provisional publication, changed authoritative score,
record correction, confirmed export, immutable evidence, restart/replay, invalid
identity/source/statistics, retained verified results during secondary disputes,
and writer conflicts. They do not demonstrate live feed permission or production
publication latency. Live source enablement and merge still require their separate
approvals. Issue #74 remains open.

## Existing watcher and publication wiring

Production remains disabled twice: `RAPID_RESULTS_ENABLED` defaults false in the
existing watcher workflow, and `operations/rapid-sources.json` has `enabled:false`.
No source endpoint is contacted by this bridge. An authorized adapter must write
canonical batches to `operations/rapid-inbox.json` on main; source URLs must match
the registry exactly. Adapter credentials stay server-side. Do not enable ESPN
or another endpoint without documented rights. The registry itself is reviewed
code/configuration, not a source-supplied assertion.

When enabled after approval, the existing watcher checks this trusted GitHub
inbox every two minutes, including periods when CFBD quota prevents acquisition.
A new immutable batch ID dispatches the existing refresh workflow's `rapid_only`
job. That job receives no CFBD credential and does no sports-provider retrieval.
It shares the existing `cfb-2026-refresh` concurrency lock and
`publish_refresh_snapshot.sh` current-main overlap/rebase protection. Its commit
triggers the existing dashboard workflow; Vite copies the public artifact.
The watcher acknowledges a batch only after its ID appears in the public
`fast-results.json`. It retries an unobserved publication once after 20 minutes,
then alerts in its event ledger; a successful workflow alone is insufficient.
Published IDs suppress duplicate publication across watcher handoffs. Failed
unpublished batches can be retried by a later session; intake remains idempotent.

Every ordinary successful CFBD refresh reconciles stored rapid events using the
already retrieved normalized snapshot, without another API request. State,
confirmed revision archives and public output are staged with the existing
validated data bundle. If the registry is disabled the reconciliation step skips.
The public provisional view never replaces authentic pregame forecasts or
canonical model input files. Source availability is not inferred from inbox or
workflow timestamps. The offline CI job exercises controlled fixtures and makes
no claim of live permission, source latency or production deployment.

Rapid batches are immutable files `operations/rapid-inbox/<batch_id>.json`.
The `rapid-inbox.json` pointer identifies the next batch; write the immutable
file before advancing it. IDs contain only letters, digits, underscores and
hyphens, start with a letter/digit, and have at most128 characters. Never reuse
an ID with different bytes. The watcher resolves the pointer to that file and
passes `rapid_batch` to publication. A queued publication therefore processes
exactly its detected batch even when the pointer advances. Later ordinary CFBD
refreshes use `--reconcile-only`, ignoring inbox contents. Pending batches must
remain discoverable to the authorized adapter until publicly acknowledged;
do not discard an unobserved batch when advancing a pointer.

Use `rapid-inbox.json` as the durable append-only index
`{"batch_ids":["batch-a","batch-b"]}` rather than replacing a latest pointer.
The watcher chooses the first ID not acknowledged by the public artifact and
loads its immutable file. Thus even a batch arriving entirely between watcher
checks remains discoverable. Retain every index ID and immutable batch file;
never remove queued IDs merely because a newer result arrived. Legacy single
`batch_id` is accepted for migration but is not the production adapter contract.

A batch that fails both publication attempts alerts and is skipped for the
remainder of that watcher session, allowing unrelated indexed batches to proceed.
The immutable batch remains in the index for a later session's recovery attempt.
