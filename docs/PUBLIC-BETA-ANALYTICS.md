# Public beta analytics — PostHog

This is an opt-in operational enhancement to the released Version 6 app. It does
not merge the separate reliability fix in PR #29, start another version, alter
football calculations/data, or authorize a production merge.

## Implementation and event contract

The app uses PostHog's documented public batch capture API directly. No SDK,
autocapture, replay, surveys, fingerprinting, DOM recording, identify/alias calls
or external scripts are installed. No dependency was added. Event properties are
constructed explicitly; search text, favorites, URLs/referrers, names/email,
exception messages/stacks and full user agents are not collected. Only canonical
school names from the published rankings can be sent by profile/comparison hooks.

| Event | Trigger / allowed product properties |
| --- | --- |
| `cfa_visit_started` | First event in an opted-in visit; once across reloads |
| `cfa_page_view` | Changed view, school or Profile section; view/section/previous_view; canonical team and section where applicable |
| `cfa_team_profile_opened` | Enter Profile or change its school; canonical team |
| `cfa_rankings_viewed` | Enter model, AP, Coaches or stock view |
| `cfa_predictions_viewed` | Enter full predictions or Profile schedule |
| `cfa_comparison_viewed` | Two different valid schools and venue selected; changes count again |
| `cfa_scenario_started` | Existing worker computation starts; random run_id and picks_count |
| `cfa_scenario_completed` | Existing worker returns success; same run_id; at most once |
| `cfa_application_error` | Fixed report/scenario/uncaught/unhandled category, view and section; no error text; each category/view throttled to once/minute |

Common properties: schema version, `traffic_type`, coarse mobile/tablet/desktop
viewport category, browser/PWA display mode, consent scope, return-visit boolean,
random session ID, event sequence and random insertion ID. PostHog receives
`$process_person_profile=false`, `$geoip_disable=true`, `$ip=null`. The latter
properties do **not** replace server-side IP discard: project verification below
is required before activation. Random IDs are pseudonymous, not a claim of
absolute anonymity; requests necessarily reach PostHog's network.

A 400 ms memory-only batch holds at most 20 events. Each request has a 2.5 s abort
timeout, excludes credentials/referrer and is never awaited by app navigation.
There are no retries or disk-backed offline queues. Offline/opt-out drops pending
events; opt-out aborts pending requests. A page lifetime caps event production at
1,000. Counts are best-effort, affected by blockers, offline periods and opt-out.

## Consent and storage

Menu → **Usage analytics** is visible beside the existing About & privacy menu.
Defaults are off. GPC or DNT=1 overrides consent and prevents capture. Turning off
clears analytics IDs and queued events without changing saved schools. Existing
PostHog events cannot be remotely erased merely by changing this browser setting.

- **Allow this visit only:** identifier/consent in tab session storage (memory
  fallback when blocked), random ID replaced after 30 minutes of inactivity;
  no persistent visitor ID. Same-tab reloads retain the visit, not duplicate it.
- **Allow repeat-visit measurement:** separate affirmative choice; random browser
  ID expires after 30 days without silent renewal. Session IDs still rotate after
  inactivity. Other browser profiles/devices remain separate. Expiry turns this
  mode off. Clearing storage breaks continuity; shared devices are not people.
- Consent preference alone may be saved in local storage; it carries no identity.
  Other tabs honor a persisted opt-out through storage events.

Tracking needs a real public project token plus its correct regional ingestion
host. Empty values disable capture. Secret-shaped keys, unknown hosts and incomplete
settings also fail the build before any token can be embedded in JavaScript.
Defaults contain
no credentials. No personal or secret project API key may enter Vite, frontend
files, GitHub variables exposed to the build, or public artifacts.

## One private owner dashboard

`ops/posthog/dashboard.json` contains 12 named insights: visitors/visits, repeat
usage, popular schools, popular sections, mobile/desktop/PWA usage, comparisons,
rankings/predictions, simulator starts/completions, aggregate navigation edges,
observed last pages, error trends and controlled test traffic.

All fan metrics filter `traffic_type='beta'`; a separate tile shows test traffic.
Visitors are approximate consenting browsers/visits, not unique people. Cross-visit
metrics only describe the separate repeat-measurement cohort. Last page and
unfinished simulation counts are directional: cancellations, blockers, opt-out
and dropped events can look like abandonment. The dashboard exposes aggregate
journeys, not a list of identifiable fans. SQL/query execution in a real project
must still be verified before claiming a working dashboard.

The owner selected US project **737110**:
https://us.posthog.com/project/737110 . The app connection was previously declined;
a signed-in PostHog browser can be used for dashboard setup without a personal API
key. At this preparation checkpoint the project requires sign-in and no live
dashboard or ingestion has been verified.

## Owner configuration needed

The public token is now reported saved by the owner. The controlled Actions
verification checks actual deployment-secret access without reading its value
back into chat. Follow [direct PostHog setup](POSTHOG-DIRECT-SETUP.md) to complete
the private dashboard without the ChatGPT connection or a personal API key.


1. The target is US PostHog project **737110**. Keep project membership to the
   owner/explicit trusted maintainers; do not create a public share link.
2. In Project settings enable **Discard client IP data**; disable session replay,
   autocapture, exception autocapture and unnecessary location enrichment. Confirm
   event retention appropriate to the beta (prefer 30 days if your plan supports
   it; otherwise record the actual retention and deletion process). These settings
   and owner access must be verified in a signed-in project.
3. Dashboard setup for this request uses the signed-in PostHog website and the
   reviewed 12-insight manifest. **No personal API key is requested or needed.**
   The optional administrative provisioner remains a separately owner-run utility;
   it is not required for this browser-based setup.
4. Enter the **public project token** only in GitHub:
   - Open `landrumc16/College-Football-Analytics` → **Settings** →
     **Secrets and variables** → **Actions** → **Secrets**.
   - Choose **New repository secret**.
   - **Name:** `POSTHOG_PUBLIC_KEY`.
   - **Secret:** paste the public project token from project 737110's settings.
   - Choose **Add secret**. Do not paste it in chat, an issue or PR comment.
   No host variable is necessary: the Pages build selects
   `https://us.i.posthog.com` when this secret is present, and leaves analytics
   unconfigured when it is absent. Never enter a personal API key. The Vite build
   rejects non-public key types before bundling. GitHub masks repository secrets
   in Actions logs; the intended public token is still included in the browser
   bundle as required for capture and is not an administrative credential.
5. Request owner merge approval after acceptance. PR #29 remains separately
   awaiting approval; this PR neither incorporates it nor changes its NO-GO.

## Acceptance and controlled activation

Local/unit and CI checks cover exact event payloads/allowlist, consent gating,
GPC/DNT, repeat expiry, duplicate suppression, blocked/corrupted storage, transport
failure, offline interruptions, canonical schools, paired simulator runs, all
375/390/430/768/1536 widths, and existing browser/PWA/regression tests. PostHog
requests are intercepted with a visibly fake test token; **no live ingestion is
claimed by those tests**. Bundle gzip growth is capped at 10 KiB over the exact
production source; no SDK is added. The live-vs-published scenario tolerance check uses the matching current packet;
immutable retained fixtures still verify exact Python/browser parity. Raw results, screenshots and exact tested SHA
are retained in the acceptance artifact and PR receipt.

After the project is configured and merge is explicitly approved, use
`?analytics_test=1` on the live URL, opt in, and perform one controlled journey:
Home → Rankings → Texas Tech Profile → Schedule → Compare → Playoffs → run a
scenario. Confirm paired run IDs and once-only events in PostHog; run the 12
queries, verify all beta tiles exclude test events, verify private dashboard access
while logged out, and turn analytics off. A fresh browser profile must send nothing
until consent. Confirm IP/person/URL properties absent from ingested test events,
replay disabled and GPC/DNT blocked. Clear test browser storage afterward.

Analytics activation is not finished until the owner can open the private
PostHog dashboard, these controlled live checks pass and production reliability
approval/deployment is complete. No analytics code is merged by this preparation.

Official references checked for this implementation:
- https://posthog.com/docs/api/capture
- https://posthog.com/docs/data/anonymous-vs-identified-events
- https://posthog.com/docs/privacy/data-collection
- https://posthog.com/docs/api/dashboards
- https://posthog.com/docs/api/insights

## Live-delivery verification boundary

The owner-authorized `deployment-secret-and-live-capture` job runs only on pushes
to the dedicated development branch. It builds with the actual repository secret
through exactly the deployment's environment references and uses one local
Chromium visitor to exercise consent, rankings, profiles/schedules, comparisons,
predictions and a completed playoff simulation. All outbound captures are marked
`traffic_type=test`; all other external browser traffic is blocked. No live fan
traffic or public GitHub Pages load is generated. Opt-out stops further requests.

The job stores only sanitized access booleans, HTTP/API acceptance, event names,
random insertion/session IDs and the source SHA. No raw bodies, token, browser
trace, cookies or compiled bundle are uploaded. Capture acceptance is a delivery
check, not private dashboard access: the owner must match those session IDs in
project 737110 and complete the dashboard/privacy checks in the direct setup guide.
