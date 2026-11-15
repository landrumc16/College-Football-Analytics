# Set up the fan-beta dashboard directly in PostHog

Project: **737110 (US)** — https://us.posthog.com/project/737110 .
No ChatGPT connection or personal API key is required.

## 1. Confirm the controlled delivery

The Actions job **deployment-secret-and-live-capture** uses the same repository
secret and host expressions as the deployment build. Its artifacts contain
`secret-access.json` and `delivery.json`; neither records the token. A PASS means
the real capture API accepted events from the actual isolated PR build. It does
not prove that you are viewing the matching project or that private queries work.

In project 737110, open a SQL insight using the SQL editor and run:

```sql
SELECT timestamp, event,
       properties.$session_id AS verification_session,
       properties.traffic_type AS traffic
FROM events
WHERE timestamp >= now() - INTERVAL 1 DAY
  AND event LIKE 'cfa_%'
  AND properties.traffic_type = 'test'
ORDER BY timestamp DESC
LIMIT 100
```

Match `verification_session` to the `sessionIds` in `delivery.json`. Allow a short
processing delay and refresh once if necessary. This is the private-project
attribution/ingestion check. Do not paste any token or private API key into the
SQL editor. These are deliberately controlled test events, not real beta fans.

## 2. Create one private dashboard

1. Use **Dashboards → New Dashboard → Blank Dashboard**.
2. Name it **College Football Analytics — Fan Beta**.
3. Open **Share** and keep public sharing **off**. Review project membership so
   only you and explicitly trusted maintainers have access. Do not create a
   public link or embed it in the football application.
4. Add each saved SQL insight below to this dashboard. From the SQL editor,
   paste one query, run it, save it with the given title, and select this
   dashboard. An existing saved insight can also be added through the dashboard's
   **Add a chart / Add insight** controls (labels vary by interface version).

All 12 queries below are copied verbatim from the reviewed
`ops/posthog/dashboard.json`. No new metrics or calculations have been invented.
The fan tiles filter `traffic_type = 'beta'`. Before release they can legitimately
show zero rows; the final controlled-test tile should show the verification
activity. Successful queries with zero fan data are not ingestion failures.

## 3. Privacy and activation checks

- In project settings enable **Discard client IP data**; turn session replay,
  autocapture and exception autocapture off. The app has no replay/autocapture SDK,
  but verify these server settings too. Review event retention for the beta.
- Open the dashboard URL in a logged-out/incognito window. It must require
  authentication rather than exposing chart data. Do not enable public sharing
  to perform this check.
- Run/refresh every insight. Confirm the controlled-test tile has test activity
  and no fan tile includes those test events. The ingestion host is US; there is
  no need for an additional GitHub host variable.
- Report only the private dashboard URL and whether the session/query/privacy
  checks passed. No token screenshot, ChatGPT connection or personal API key is
  needed.

PR #30 is still subject to explicit owner merge approval. Adding the secret and
sending controlled isolated tests does not deploy analytics to production. After
approval and deployment, repeat one real application journey with
`?analytics_test=1`, verify the new events here and confirm opt-out/PWA recovery.
The separately unmerged reliability PR #29 remains a beta-readiness hold.

## Dashboard insights (paste each SQL query into its own saved insight)

### 1. Visitors and visits

Consenting browsers only. Visit-only IDs count as separate visitors; not a census of fans.

```sql
SELECT uniq(distinct_id) AS participating_browsers_or_visits, uniq(properties.$session_id) AS visits FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_visit_started'
```

### 2. Repeat visits

Only browsers that separately allow 30-day repeat measurement. Clearing storage resets this estimate.

```sql
SELECT toDate(timestamp) AS day, count() AS visits, countIf(properties.return_visit = true) AS repeat_visits FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_visit_started' AND properties.identity_scope = 'returning' GROUP BY day ORDER BY day
```

### 3. Popular schools

Profiles opened, not saved favorites or typed searches.

```sql
SELECT properties.team AS school, count() AS profile_opens FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_team_profile_opened' GROUP BY school ORDER BY profile_opens DESC LIMIT 20
```

### 4. Popular sections

Intentional page transitions. Re-selecting the same page does not count again.

```sql
SELECT properties.section AS section, properties.view AS page, count() AS views FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_page_view' GROUP BY section, page ORDER BY views DESC
```

### 5. Mobile and desktop use

Coarse viewport categories, including tablet. Not device fingerprinting.

```sql
SELECT properties.device_type AS screen, properties.display_mode AS app_or_browser, uniq(properties.$session_id) AS visits FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_page_view' GROUP BY screen, app_or_browser ORDER BY visits DESC
```

### 6. Team comparisons

Valid two-school selections only; changes in venue count as another comparison.

```sql
SELECT properties.team AS first_school, properties.opponent AS second_school, count() AS comparisons FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_comparison_viewed' GROUP BY first_school, second_school ORDER BY comparisons DESC LIMIT 20
```

### 7. Rankings and predictions

Published section views; no query text or prediction math is captured.

```sql
SELECT event AS activity, properties.view AS page, count() AS views FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event IN ('cfa_rankings_viewed','cfa_predictions_viewed') GROUP BY activity, page ORDER BY views DESC
```

### 8. Simulator starts and completions

Counts by run ID. Canceled computations, navigation away, blockers and lost events can leave a start without completion; this is not automatically an app error.

```sql
SELECT uniqIf(properties.run_id,event = 'cfa_scenario_started') AS starts, uniqIf(properties.run_id,event = 'cfa_scenario_completed') AS completions FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event IN ('cfa_scenario_started','cfa_scenario_completed')
```

### 9. Navigation journeys

Aggregate page-to-page transitions; no person or individual-session list.

```sql
SELECT properties.previous_view AS from_page, properties.view AS to_page, count() AS transitions FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_page_view' AND properties.previous_view IS NOT NULL GROUP BY from_page, to_page ORDER BY transitions DESC LIMIT 30
```

### 10. Last page in a visit

Observed last pages, not proven dissatisfaction. Visits ending in the last 30 minutes are omitted; opt-out, blockers and dropped events affect this estimate.

```sql
SELECT last_page, count() AS visits_ending_here FROM (SELECT properties.$session_id AS visit, argMax(properties.view,timestamp) AS last_page, max(timestamp) AS last_seen FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_page_view' GROUP BY visit HAVING last_seen < now() - INTERVAL 30 MINUTE) GROUP BY last_page ORDER BY visits_ending_here DESC
```

### 11. Error trends

Broad fixed categories only. Exception text, stacks, resource URLs and search strings are never sent.

```sql
SELECT toDate(timestamp) AS day, properties.error_kind AS category, properties.view AS page, count() AS reports FROM events WHERE timestamp >= now() - INTERVAL 30 DAY AND properties.traffic_type = 'beta' AND event = 'cfa_application_error' GROUP BY day, category, page ORDER BY day DESC
```

### 12. Controlled test traffic

Deliberately excluded from every beta tile above. Use ?analytics_test=1 for production verification; no traffic is fabricated by setup.

```sql
SELECT event, count() AS test_events FROM events WHERE timestamp >= now() - INTERVAL 7 DAY AND properties.traffic_type = 'test' AND event LIKE 'cfa_%' GROUP BY event ORDER BY test_events DESC
```

## Official PostHog instructions

- https://posthog.com/docs/sql
- https://posthog.com/docs/product-analytics/dashboards
- https://posthog.com/docs/product-analytics/insights
- https://posthog.com/docs/product-analytics/sharing
- https://posthog.com/docs/privacy/data-collection
