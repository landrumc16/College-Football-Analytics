"""Data freshness monitor: find stale or unmonitored data without relying on anyone noticing it.

Each pass reads only the GitHub API, the live site and the free official CFP page (no CFBD calls) and reports:
- missed scheduled executions (a cron fire time over an hour ago with no scheduled run since),
- a stopped watcher chain (monitoring needed but no watcher running or queued),
- unpublished official releases (CFP page out but not on the site; AP/Coaches poll overdue),
- completed games awaiting publication (past their latest finish time but not final on the site),
- exhausted CFBD budgets (from the watcher's live quota reading),
- failed deployments (latest Pages deployment failed and not superseded by a success).

Alerts are kept in one GitHub issue ("Data freshness alert"): opened when the first alert appears, updated and commented
only when the set of alerts changes, and closed when everything is resolved. The issue body carries a machine-readable
block. Each deployment writes monitor-status.json (watcher state + those alerts) next to the app, and a change in the
alerts triggers a redeployment, so the published "Data status" never says "all current" while a release is overdue or a
known problem is open, without the site contacting any third party. Run by the watcher every 10 minutes and by
watch_keeper from other workflows.

  python -m cfb_analytics.freshness_monitor --site-status web/dist/monitor-status.json   # used by dashboard.yml
"""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import cfp_publish
from . import event_calendar as cal

ISSUE_TITLE = "Data freshness alert"
MARKER = re.compile(r"<!-- freshness-status (\{.*?\}) -->", re.S)
WORKFLOWS = {"event-watcher.yml": "Event-driven game-day watcher", "refresh-data.yml": "Refresh college football data",
             "refresh-polls.yml": "Refresh official college football polls", "dashboard.yml": "Build and publish analytics dashboard",
             "v8-stats-refresh.yml": "Refresh V8 offense and defense statistics"}
SCHEDULE_GRACE = timedelta(minutes=60)    # GitHub normally starts scheduled runs within ~15 minutes
HANDOFF_GRACE = timedelta(minutes=10)     # a chained successor starts within seconds; allow for queueing
CFP_GRACE = timedelta(minutes=10)         # official page out this long without publication -> alert
GAME_GRACE = timedelta(minutes=30)        # after a game's latest finish time
RELEASE_FLOOR = 8                         # matches event_watcher.RELEASE_FLOOR (kept here to avoid an import cycle)


def _t(value):
    return cal.parse_time(value)


# ---- cron ------------------------------------------------------------------------------------------------------------
def _field(spec, lo, hi):
    out = set()
    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, step = part.split("/")
            step = int(step)
        if part == "*":
            a, b = lo, hi
        elif "-" in part:
            a, b = map(int, part.split("-"))
        else:
            a = b = int(part)
        out.update(range(a, b + 1, step))
    return out


def cron_matches(expr, t):
    """True when the 5-field UTC cron expression fires at minute t (GitHub semantics; day-of-week 0 = Sunday)."""
    minute, hour, dom, month, dow = expr.split()
    dows = {d % 7 for d in _field(dow, 0, 7)}
    day_ok = t.day in _field(dom, 1, 31)
    dow_ok = (t.isoweekday() % 7) in dows
    day = (day_ok and dow_ok) if dom == "*" or dow == "*" else (day_ok or dow_ok)
    return t.minute in _field(minute, 0, 59) and t.hour in _field(hour, 0, 23) and t.month in _field(month, 1, 12) and day


def last_fire(exprs, now, lookback=timedelta(hours=30)):
    """Most recent fire time at or before `now` for any of the cron expressions, within the lookback."""
    t = now.replace(second=0, microsecond=0)
    stop = t - lookback
    while t >= stop:
        if any(cron_matches(e, t) for e in exprs):
            return t
        t -= timedelta(minutes=1)
    return None


def workflow_crons(directory=Path(".github/workflows")):
    out = {}
    for name in WORKFLOWS:
        path = directory / name
        if path.exists():
            crons = re.findall(r"cron:\s*'([^']+)'", path.read_text())
            if crons:
                out[name] = crons
    return out


# ---- assessment ------------------------------------------------------------------------------------------------------
def _alert(key, area, severity, text):
    return {"key": key, "area": area, "severity": severity, "text": text}


def assess(now, *, runs, crons, snapshot, live_report=None, live_polls=None, official_cfp_exists=None, quota=None,
           watcher_running=False, watcher_alerts=()):
    """Alerts for the current state. `runs` maps workflow file -> recent runs (GitHub API rows, newest first)."""
    alerts = []
    # Missed scheduled executions.
    for workflow, exprs in crons.items():
        due = last_fire(exprs, now - SCHEDULE_GRACE)
        if due is None:
            continue
        started = [r for r in runs.get(workflow, []) if r.get("event") == "schedule" and (_t(r.get("created_at")) or now) >= due - timedelta(minutes=2)]
        if not started:
            alerts.append(_alert(f"missed-schedule:{workflow}", "Scheduling", "warning",
                                 f"{WORKFLOWS[workflow]}: the scheduled run due at {due:%b %d %H:%M} UTC has not started "
                                 f"({int((now - due).total_seconds() // 60)} minutes late)"))
    # Stopped watcher chain.
    needed = cal.horizon_active(snapshot, now)
    watcher_runs = runs.get("event-watcher.yml", [])
    active = watcher_running or any(r.get("status") in ("queued", "pending", "waiting", "requested", "in_progress") for r in watcher_runs)
    last_end = max((_t(r.get("updated_at")) for r in watcher_runs if _t(r.get("updated_at"))), default=None)
    if needed and not active and (last_end is None or now - last_end > HANDOFF_GRACE):
        since = f" since {last_end:%b %d %H:%M} UTC" if last_end else ""
        alerts.append(_alert("watcher-stopped", "Live monitoring", "critical",
                             f"No event watcher is running or queued{since} while games or releases are due"))
    # Unpublished official CFP release.
    polls = live_polls or {}
    published = polls.get("cfp_published_at")
    day = cfp_publish.due_release(now, datetime.fromisoformat(published).date() if published else None)
    if day is not None:
        announced = datetime(day.year, day.month, day.day, 10 if day.weekday() == 6 else 17, tzinfo=cal.CENTRAL)
        if official_cfp_exists and now - announced > CFP_GRACE:
            alerts.append(_alert(f"cfp-unpublished:{day}", "CFP rankings", "critical",
                                 f"The official {day:%b %d} CFP rankings are out but not yet published on the site"))
        elif official_cfp_exists is False and now - announced > timedelta(hours=3):
            alerts.append(_alert(f"cfp-not-found:{day}", "CFP rankings", "warning",
                                 f"The {day:%b %d} CFP release is due but its official page was not found"))
    # Overdue AP/Coaches polls.
    if cal.poll_window(now) == "overdue":
        week = cal.expected_poll_week(snapshot, now)
        weeks = polls.get("poll_weeks", {})
        for key, area in (("ap_top25", "AP Poll"), ("coaches_top25", "Coaches Poll")):
            if week and (weeks.get(key) or 0) < week:
                alerts.append(_alert(f"poll-overdue:{key}:{week}", area, "critical",
                                     f"The week {week} {area} is overdue (site shows week {weeks.get(key) or 'none'})"))
    # Completed games awaiting publication.
    live_schedule = {g.get("game_id"): g for g in (live_report or {}).get("schedule", [])}
    retrieved = _t((live_report or {}).get("retrieved_at"))
    waiting = []
    for g in snapshot.get("games", []):
        k = _t(g.get("start_date"))
        if k is None or g.get("season_type") == "postseason":
            continue
        finish = k + cal.LATE_FINISH
        site = live_schedule.get(g.get("game_id"))
        if site and not site.get("completed") and finish + GAME_GRACE <= now <= finish + cal.OVERDUE_LIMIT and (retrieved is None or retrieved < finish):
            waiting.append(g)
    if waiting and live_report is not None:
        names = ", ".join(f"{g.get('away')} at {g.get('home')}" for g in waiting[:3])
        alerts.append(_alert("games-awaiting", "Scores and records", "critical",
                             f"{len(waiting)} overdue game result(s) not yet published ({names}{'…' if len(waiting) > 3 else ''}); "
                             "completion is not verified by this time-based check"))
    # CFBD budget.
    if quota and "remaining" in quota:
        if quota["remaining"] <= RELEASE_FLOOR:
            alerts.append(_alert("quota-floor", "Data source", "critical",
                                 f"CFBD quota nearly exhausted ({quota['remaining']} calls left until reset): automatic detection stopped"))
        elif quota.get("spendable", 1) <= 0:
            alerts.append(_alert("quota-discretionary", "Data source", "warning",
                                 f"Discretionary CFBD budget exhausted ({quota['remaining']} calls left, {quota.get('days_to_reset')} days to reset): "
                                 "game results are published in fewer waves; releases use the priority allowance"))
    # Failed deployment (not superseded by a later success).
    deploys = [r for r in runs.get("dashboard.yml", []) if r.get("status") == "completed" and r.get("head_branch") == "main"
               and r.get("conclusion") in ("success", "failure")]
    if deploys:
        latest = max(deploys, key=lambda r: _t(r.get("created_at")) or now)
        if latest.get("conclusion") == "failure":
            alerts.append(_alert("deploy-failed", "Publishing", "critical",
                                 f"The latest site deployment failed ({latest.get('html_url', 'run ' + str(latest.get('id')))})"))
    for text in watcher_alerts:
        severity = "critical" if text.startswith(("ESPN reports a final", "Publication quota")) else "warning"
        alerts.append(_alert(f"watcher:{text[:60]}", "Live monitoring", severity, text))
    return alerts


# ---- issue -----------------------------------------------------------------------------------------------------------
def issue_body(alerts, now):
    status = {"updated_at": now.isoformat(timespec="seconds"),
              "alerts": [{k: a[k] for k in ("key", "area", "severity", "text")} for a in alerts]}
    rows = "\n".join(f"| {a['severity']} | {a['area']} | {a['text']} |" for a in alerts)
    return (f"Automatic data freshness monitor. Updated {now:%Y-%m-%d %H:%M} UTC.\n\n| Severity | Area | Problem |\n| --- | --- | --- |\n{rows}\n\n"
            "This issue closes itself when every problem is resolved. See docs/EVENT-DRIVEN-DATA.md for the runbook.\n\n"
            f"<!-- freshness-status {json.dumps(status)} -->\n")


def keys_of(body):
    m = MARKER.search(body or "")
    return sorted(a["key"] for a in json.loads(m.group(1))["alerts"]) if m else None


def open_issue(github):
    return next((i for i in github("issues?state=open&per_page=50") or [] if i.get("title") == ISSUE_TITLE and "pull_request" not in i), None)


def issue_alerts(issue):
    m = MARKER.search((issue or {}).get("body") or "")
    return json.loads(m.group(1))["alerts"] if m else []


def sync_issue(github, alerts, now, log=print, keep=()):
    """Open, update or close the single alert issue; comment only when the set of alerts changes.

    `keep` lists key prefixes this caller cannot evaluate (a keeper has no CFBD quota reading and no watcher alerts):
    such alerts already in the issue are carried over instead of being cleared, so callers with different views never
    make the issue flip back and forth."""
    issue = open_issue(github)
    known = {a["key"] for a in alerts}
    alerts = list(alerts) + [a for a in issue_alerts(issue) if a["key"].startswith(tuple(keep)) and a["key"] not in known] if keep else list(alerts)
    keys = sorted(a["key"] for a in alerts)
    if not alerts:
        if issue:
            github(f"issues/{issue['number']}/comments", "POST", {"body": f"All freshness checks pass as of {now:%Y-%m-%d %H:%M} UTC. Closing."})
            github(f"issues/{issue['number']}", "PATCH", {"state": "closed", "state_reason": "completed",
                                                          "body": issue_body([], now)})
            log(f"freshness: closed issue #{issue['number']}")
            return "closed"
        return "clear"
    if issue is None:
        created = github("issues", "POST", {"title": ISSUE_TITLE, "body": issue_body(alerts, now)})
        log(f"freshness: opened issue #{(created or {}).get('number')} with {len(alerts)} alert(s)")
        return "opened"
    if keys_of(issue.get("body")) != keys:
        github(f"issues/{issue['number']}", "PATCH", {"body": issue_body(alerts, now)})
        github(f"issues/{issue['number']}/comments", "POST",
               {"body": "Alerts changed:\n\n" + "\n".join(f"- **{a['severity']}** {a['area']}: {a['text']}" for a in alerts)})
        log(f"freshness: updated issue #{issue['number']} ({len(alerts)} alert(s))")
        return "updated"
    return "unchanged"


# ---- one pass ----------------------------------------------------------------------------------------------------------
def run_pass(providers, *, now=None, snapshot, quota=None, watcher_alerts=None, watcher_running=True, log=print, report=True, crons=None):
    """Collect state (GitHub API, live site, official CFP page; no CFBD calls), assess and sync the issue.

    quota=None or watcher_alerts=None means this caller cannot evaluate those alerts (a keeper): existing ones are kept.
    The site is redeployed only when the critical alerts change, because only those (and the watcher state) appear
    in its Data status."""
    now = now or datetime.now(timezone.utc)
    runs = {}
    for workflow in WORKFLOWS:
        try:
            runs[workflow] = providers.workflow_runs(workflow, 30)
        except Exception as error:
            log(f"freshness: runs for {workflow} unavailable: {str(error)[:120]}")
    live_report = live_polls = None
    try:
        live_report = providers.live_report()
    except Exception as error:
        log(f"freshness: live report unavailable: {str(error)[:120]}")
    try:
        live_polls = providers.live_polls()
    except Exception as error:
        log(f"freshness: live polls unavailable: {str(error)[:120]}")
    official = None
    published = (live_polls or {}).get("cfp_published_at")
    day = cfp_publish.due_release(now, datetime.fromisoformat(published).date() if published else None)
    if day is not None:
        try:
            official = providers.cfp_page(cfp_publish.official_url(day)) is not None
        except Exception as error:
            log(f"freshness: official CFP page unavailable: {str(error)[:120]}")
    alerts = assess(now, runs=runs, crons=workflow_crons() if crons is None else crons, snapshot=snapshot, live_report=live_report, live_polls=live_polls,
                    official_cfp_exists=official, quota=quota, watcher_running=watcher_running, watcher_alerts=watcher_alerts or ())
    for a in alerts:
        log(f"freshness {a['severity']}: {a['area']}: {a['text']}")
    if report:
        keep = (("quota-",) if quota is None else ()) + (("watcher:",) if watcher_alerts is None else ())
        try:
            critical = lambda items: sorted(a["key"] for a in items if a["severity"] == "critical")
            before = critical(issue_alerts(open_issue(providers.github)))
            if sync_issue(providers.github, alerts, now, log, keep) != "unchanged" and critical(alerts) != before:
                providers.dispatch("dashboard.yml")       # republish monitor-status.json so the site reflects it
                log("freshness: critical alerts changed; site redeployment requested")
        except Exception as error:
            log(f"freshness: could not update the alert issue: {str(error)[:200]}")
    return alerts


def site_status(providers, now, snapshot):
    """monitor-status.json for the site: watcher state and the monitor's open alerts (from its issue)."""
    status = {"generated_at": now.isoformat(timespec="seconds"), "watcher": {"state": "unknown", "last_run_at": None}, "alerts": []}
    try:
        runs = providers.workflow_runs("event-watcher.yml", 5)
        ended = [t for r in runs if (t := _t(r.get("updated_at")))]
        status["watcher"]["last_run_at"] = max(ended).isoformat() if ended else None
        if any(r.get("status") in ("queued", "pending", "waiting", "requested", "in_progress") for r in runs) or (ended and now - max(ended) <= HANDOFF_GRACE):
            status["watcher"]["state"] = "active"
        else:
            status["watcher"]["state"] = "stopped" if cal.horizon_active(snapshot, now) else "idle"
    except Exception as error:
        status["watcher"]["error"] = str(error)[:120]
    try:
        issue = next((i for i in providers.github("issues?state=open&per_page=50") or []
                      if i.get("title") == ISSUE_TITLE and "pull_request" not in i), None)
        m = MARKER.search((issue or {}).get("body") or "")
        status["alerts"] = json.loads(m.group(1))["alerts"] if m else []
    except Exception as error:
        status["alerts_error"] = str(error)[:120]
    return status


def main(argv=None):
    import argparse
    import os
    from .event_watcher import Providers
    from .watch_keeper import load_snapshot
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-status", type=Path, required=True)
    args = ap.parse_args(argv)
    providers = Providers("", os.environ.get("GITHUB_TOKEN", ""))
    status = site_status(providers, datetime.now(timezone.utc), load_snapshot())
    args.site_status.write_text(json.dumps(status, indent=1) + "\n")
    print(json.dumps(status))


if __name__ == "__main__":
    main()
