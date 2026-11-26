"""Permanent data-freshness reliability (November 24 CFP incident follow-up).

Acceptance scenarios, each driving the real code paths with a simulated clock, CFBD, GitHub and live site:
- GitHub scheduling interruption: the watcher chain alone covers 48 hours of games and a CFP release with no cron.
- Zero discretionary CFBD quota: the official CFP page is still read (free) and the release confirmed and published
  from the priority allowance within five minutes.
- Delayed secondary-source confirmation: CFBD lags the official page; confirmation retries with back-off, then publishes
  (or alerts without publishing if CFBD never agrees).
- Duplicate watcher execution: a second concurrent watcher exits; at most one successor is ever queued.
- Failed deployment: re-dispatch then alert (watcher); a failed Pages deployment raises an alert unless superseded.
- Complete watcher-chain interruption: the keeper restarts it from any workflow; the monitor reports it.
"""
from datetime import datetime, timedelta, timezone

from test_event_driven import FakeProviders, T0, TEAMS, game, setup

from cfb_analytics import event_calendar as cal
from cfb_analytics import freshness_monitor as fm
from cfb_analytics import poll_refresh
from cfb_analytics.event_watcher import (CFP_CONFIRM_MAX, CFP_RELEASE_COST, MAX_STARTS_PER_HOUR, RELEASE_FLOOR, Watcher,
                                         chain_successor, quota_plan)
from cfb_analytics.watch_keeper import ensure_watcher

TUESDAY = datetime(2026, 11, 24, 23, 55, tzinfo=timezone.utc)      # 17:55 Central on the 24 November release day
RELEASED = datetime(2026, 11, 25, 0, 3, tzinfo=timezone.utc)        # official page appears at 18:03 Central
iso = lambda t: t.isoformat().replace("+00:00", "Z")


def cfp_events(w):
    return [e for e in w.events if e.kind == "cfp"]


# ---- independent CFP detection, priority budget, latency ------------------------------------------------------------
def test_zero_discretionary_quota_still_publishes_the_official_cfp_release_within_five_minutes():
    # Discretionary budget 0 (the real 24 November state); priority allowance covers confirmation and publication.
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=TUESDAY, budget=0, release_budget=CFP_RELEASE_COST,
                        deploy_minutes=3.5)
    p.official_at = RELEASED
    p.cfp_at = (RELEASED, 13)                    # CFBD publishes the committee poll at the same time
    w.run(TUESDAY + timedelta(hours=2))
    [e] = cfp_events(w)
    r = e.record()
    assert e.status == "published" and e.source == "official-page"
    assert r["detection_seconds_at_most"] <= 30                  # official page read every 30 s, no CFBD call
    assert r["verification_seconds"] == 0                        # CFBD agreed on the first check
    assert r["total_seconds_at_most"] <= 300                     # page out -> live site, with a 3.5-minute deployment
    assert p.cfbd_calls == 1 and w.release_spent <= w.release_budget and w.discretionary_spent == 0
    assert p.page_calls > 10                                     # reading the page cost no CFBD calls


def test_delayed_cfbd_confirmation_retries_with_backoff_then_publishes():
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=TUESDAY, budget=0, release_budget=CFP_RELEASE_COST)
    p.official_at = RELEASED
    p.cfp_at = (RELEASED + timedelta(minutes=5), 13)             # CFBD lags the official page by five minutes
    w.run(TUESDAY + timedelta(hours=2))
    [e] = cfp_events(w)
    assert e.status == "published"
    assert 5 * 60 <= e.record()["verification_seconds"] <= 8 * 60
    assert p.cfbd_calls <= CFP_CONFIRM_MAX and not w.alerts


def test_cfbd_never_confirming_is_never_published_and_alerts_within_the_call_cap():
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=TUESDAY, budget=0, release_budget=CFP_RELEASE_COST)
    p.official_at = RELEASED                                     # CFBD never lists the new committee poll
    w.run(TUESDAY + timedelta(hours=3))
    [e] = cfp_events(w)
    assert e.status == "detected" and e.confirmed_at is None and not p.dispatches
    assert p.cfbd_calls == CFP_CONFIRM_MAX and any("not confirmed" in a for a in w.alerts)
    assert "cfp_published_at" not in p.site_polls


def test_no_quota_left_alerts_instead_of_confirming():
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=TUESDAY, budget=0, release_budget=0)
    p.official_at, p.cfp_at = RELEASED, (RELEASED, 13)
    w.run(TUESDAY + timedelta(minutes=30))
    assert p.cfbd_calls == 0 and not p.dispatches and any("no CFBD calls are left" in a for a in w.alerts)


def test_quota_plan_gives_releases_a_priority_allowance_when_discretionary_is_zero():
    games = {"season": 2026, "games": [game(1, datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc), week=13),
                                       game(2, datetime(2026, 11, 25, 0, 0, tzinfo=timezone.utc), week=13)]}
    now = datetime(2026, 11, 24, 21, 3, tzinfo=timezone.utc)
    # The real 24 November reading: 40 calls left, 7 days to reset -> 0 discretionary.
    q = quota_plan({"remainingCalls": 40, "resetAt": "2026-12-01T00:00:00Z"}, games, now, {"poll_weeks": {"ap_top25": 13, "coaches_top25": 13}})
    assert q["spendable"] == 0 and q["budget"] == 0
    assert q["releases_due_today"]["cfp"] and q["priority_budget"] >= CFP_RELEASE_COST
    assert q["wave_at"] is not None                               # one end-of-day publication wave for the games
    # At the floor nothing is spent at all.
    floor = quota_plan({"remainingCalls": RELEASE_FLOOR, "resetAt": "2026-12-01T00:00:00Z"}, games, now)
    assert floor["priority_budget"] == 0 and floor["budget"] == 0


def test_end_of_day_wave_publishes_finals_when_the_discretionary_budget_is_empty():
    kickoff = T0 - timedelta(hours=1)
    clock, p, w = setup([game(1, kickoff)], budget=0, release_budget=10)
    w.wave_at = kickoff + cal.LATE_FINISH
    p.finals[1] = (kickoff + timedelta(hours=3), 31, 17)
    w.run(T0 + timedelta(hours=8))
    [e] = [e for e in w.events if e.kind == "final"]
    assert e.status == "published" and e.priority and w.discretionary_spent == 0
    assert p.cfbd_calls == 1 and w.release_spent == 1 + 4         # one check + one data refresh


def test_poll_checks_use_the_priority_allowance_at_the_poll_interval():
    sunday = datetime(2026, 11, 22, 18, 55, tzinfo=timezone.utc)     # 12:55 Central
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=sunday, budget=0, release_budget=10)
    w.poll_interval = 600
    p.polls_at = {"ap_top25": (sunday + timedelta(minutes=25), 13), "coaches_top25": (sunday + timedelta(minutes=25), 13)}
    w.run(sunday + timedelta(hours=3))
    assert {e.status for e in w.events if e.kind == "poll"} == {"published"}
    assert p.cfbd_calls <= 4 and w.release_spent <= 10


# ---- chain: handoffs, duplicates, runaway loops ----------------------------------------------------------------------
class FakeGitHub:
    """GitHub Actions concurrency for the watcher group: one running, at most one queued (a newer queued run replaces it)."""

    def __init__(self, clock):
        self.clock, self.runs, self.next_id = clock, [], 100

    def start(self, event="workflow_dispatch"):
        self.next_id += 1
        run = {"id": self.next_id, "status": "queued", "event": event, "created_at": iso(self.clock()), "updated_at": iso(self.clock())}
        for r in self.runs:
            if r["status"] == "queued":
                r["status"], r["conclusion"] = "completed", "cancelled"
        self.runs.append(run)
        if not any(r["status"] == "in_progress" for r in self.runs):
            run["status"] = "in_progress"
        return run

    def finish(self, run):
        run["status"], run["updated_at"] = "completed", iso(self.clock())
        queued = [r for r in self.runs if r["status"] == "queued"]
        if queued:
            queued[0]["status"] = "in_progress"
            return queued[0]
        return None

    def watcher_runs(self):
        return list(reversed(self.runs))

    def dispatch(self, workflow, inputs=None):
        assert workflow == "event-watcher.yml"
        self.start()


def test_chain_successor_queues_once_detects_duplicates_and_stops_a_crash_loop():
    clock = type("C", (), {"t": TUESDAY, "__call__": lambda s: s.t})()
    gh = FakeGitHub(clock)
    me = gh.start()
    assert chain_successor(gh, clock(), me["id"])[0] == "queued"
    assert chain_successor(gh, clock(), me["id"])[0] == "already queued"       # never a second queued successor
    assert sum(r["status"] == "queued" for r in gh.runs) == 1
    # A second watcher that somehow runs concurrently sees the earlier one and exits.
    rogue = {"id": me["id"] + 50, "status": "in_progress", "created_at": iso(clock()), "updated_at": iso(clock())}
    gh.runs.append(rogue)
    assert chain_successor(gh, clock(), rogue["id"])[0] == "duplicate"
    # Crash loop: runs ending seconds after they start stop chaining after MAX_STARTS_PER_HOUR starts.
    gh2 = FakeGitHub(clock)
    run, starts = gh2.start(), 1
    while True:
        action, _ = chain_successor(gh2, clock(), run["id"])
        clock.t += timedelta(seconds=20)
        run = gh2.finish(run)
        if run is None:
            break
        starts += 1
        assert starts <= MAX_STARTS_PER_HOUR + 2
    assert action == "rate-limited"


def test_github_scheduling_interruption_the_chain_alone_covers_48_hours():
    """No scheduled run at all for two days: one manual start, then only chained handoffs."""
    start = datetime(2026, 11, 24, 12, 0, tzinfo=timezone.utc)
    games = [game(1, datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc), week=13),
             game(2, datetime(2026, 11, 25, 0, 30, tzinfo=timezone.utc), week=13),
             game(3, datetime(2026, 11, 26, 1, 0, tzinfo=timezone.utc), week=13)]
    clock, p, _ = setup(games, start=start, deploy_minutes=3.5)
    p.finals = {1: (games_kick(games[0]) + timedelta(hours=3), 24, 21), 2: (games_kick(games[1]) + timedelta(hours=3, minutes=20), 17, 10),
                3: (games_kick(games[2]) + timedelta(hours=3, minutes=5), 35, 28)}
    p.official_at, p.cfp_at = RELEASED, (RELEASED, 13)
    gh = FakeGitHub(clock)
    run = gh.start()
    snapshot = {"season": 2026, "games": games}
    polls = {"poll_weeks": {"ap_top25": 13, "coaches_top25": 13}, "cfp_week": 12, "cfp_published_at": "2026-11-17"}
    published, runs_used, overlap = {}, 0, False
    while run and clock() < start + timedelta(hours=48):
        runs_used += 1
        overlap |= sum(r["status"] == "in_progress" for r in gh.runs) > 1
        action, _ = chain_successor(gh, clock(), run["id"]) if cal.horizon_active(snapshot, clock()) else ("off", "")
        w = Watcher(snapshot, polls, p, clock=clock, sleep=clock.sleep, active_interval=300, watch_interval=600,
                    log=lambda *_: None, cfbd_budget=400, release_budget=CFP_RELEASE_COST, known_teams=TEAMS,
                    stay_alive=action in ("queued", "already queued"))
        w.seen = {k for k in published}
        w.run(clock() + timedelta(minutes=350))
        for e in w.events:
            if e.status == "published":
                published[e.key] = e.record()
        for g in snapshot["games"]:                               # the next run starts from the refreshed snapshot
            for r in published.values():
                if r["kind"] == "final" and r["detail"]["game_id"] == g["game_id"]:
                    g.update(completed=True, home_score=r["detail"]["score"][0], away_score=r["detail"]["score"][1])
        if any(k.startswith("cfp:") for k in published):
            polls = {**polls, "cfp_published_at": "2026-11-24", "cfp_week": 13}
        run = gh.finish(run)
    assert not overlap and 6 <= runs_used <= 12
    assert {k.split(":")[0] for k in published} == {"final", "cfp"} and sum(k.startswith("final:") for k in published) == 3
    # CFP: page read every 30 s -> within five minutes. Games: bounded by the quota-paced check interval (5 min here).
    assert all(r["total_seconds_at_most"] <= 300 for k, r in published.items() if k.startswith("cfp:"))
    assert all(r["total_seconds_at_most"] <= 300 + 4 * 60 for k, r in published.items() if k.startswith("final:"))


def games_kick(g):
    return cal.parse_time(g["start_date"])


def test_a_chained_run_stays_alive_without_spending_and_an_unchained_one_ends():
    quiet = datetime(2026, 11, 23, 8, 0, tzinfo=timezone.utc)
    clock, p, w = setup([game(1, datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc), week=13)], start=quiet, stay_alive=True)
    w.run(quiet + timedelta(minutes=350))
    assert clock() >= quiet + timedelta(minutes=340) and p.cfbd_calls == 0
    clock, p, w = setup([game(1, datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc), week=13)], start=quiet)
    w.run(quiet + timedelta(minutes=350))
    assert clock() == quiet and p.cfbd_calls == 0


def test_duplicate_watchers_never_double_publish():
    clock, p, w1 = setup([game(1, T0 - timedelta(hours=3))])
    p.finals[1] = (T0, 28, 24)
    w1.run(T0 + timedelta(minutes=20))
    gh = FakeGitHub(clock)
    first = gh.start()
    second = {"id": first["id"] + 1, "status": "in_progress", "created_at": iso(clock()), "updated_at": iso(clock())}
    gh.runs.append(second)
    assert chain_successor(gh, clock(), second["id"])[0] == "duplicate"         # exits before watching
    assert [wf for _, wf in p.dispatches] == ["refresh-data.yml"]


# ---- keeper: complete chain interruption -----------------------------------------------------------------------------
def test_keeper_restarts_a_stopped_chain_but_never_a_second_watcher():
    now = TUESDAY
    calls = []
    dispatch = lambda wf, inputs=None: calls.append(wf)
    stopped = [{"id": 1, "status": "completed", "created_at": iso(now - timedelta(hours=8)), "updated_at": iso(now - timedelta(hours=2))}]
    assert ensure_watcher(stopped, now, True, dispatch) == "restarted the watcher chain" and calls == ["event-watcher.yml"]
    running = [{"id": 2, "status": "in_progress", "created_at": iso(now), "updated_at": iso(now)}]
    assert ensure_watcher(running, now, True, dispatch).startswith("watcher running")
    queued = [{"id": 3, "status": "pending", "created_at": iso(now), "updated_at": iso(now)}]
    assert ensure_watcher(queued, now, True, dispatch).startswith("watcher running")
    handoff = [{"id": 4, "status": "completed", "created_at": iso(now - timedelta(hours=6)), "updated_at": iso(now - timedelta(minutes=2))}]
    assert ensure_watcher(handoff, now, True, dispatch) == "handoff in progress"
    assert ensure_watcher(stopped, now, False, dispatch).startswith("not needed")
    loop = [{"id": i, "status": "completed", "created_at": iso(now - timedelta(minutes=5 * i)), "updated_at": iso(now - timedelta(minutes=30))}
            for i in range(MAX_STARTS_PER_HOUR + 2)]
    assert ensure_watcher(loop, now, True, dispatch).startswith("not restarted")
    assert calls == ["event-watcher.yml"]
    # A watcher that crashed before queuing its successor: its own end-of-job keeper step restarts the chain.
    crashed = [{"id": 7, "status": "in_progress", "created_at": iso(now - timedelta(minutes=1)), "updated_at": iso(now - timedelta(minutes=20))}]
    assert ensure_watcher(crashed, now, True, dispatch, me=7) == "restarted the watcher chain"


# ---- monitor ----------------------------------------------------------------------------------------------------------
def test_cron_matching_follows_github_semantics():
    sunday_17 = datetime(2026, 11, 22, 17, 15, tzinfo=timezone.utc)
    assert fm.cron_matches("*/15 16-22 * 8-12 0", sunday_17)
    assert not fm.cron_matches("*/15 16-22 * 8-12 0", sunday_17 + timedelta(days=1))
    assert fm.cron_matches("23 11 * * *", datetime(2026, 11, 24, 11, 23, tzinfo=timezone.utc))
    assert fm.cron_matches("*/15 0-5 * 11-12 3", datetime(2026, 11, 25, 1, 30, tzinfo=timezone.utc))
    assert fm.last_fire(["23 11 * * *"], datetime(2026, 11, 24, 21, 0, tzinfo=timezone.utc)) == datetime(2026, 11, 24, 11, 23, tzinfo=timezone.utc)


def _state(now, **over):
    snapshot = {"season": 2026, "games": [game(1, datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc), week=13),
                                          game(2, datetime(2026, 11, 21, 17, 0, tzinfo=timezone.utc), True, 1, 0, week=12)]}
    live_report = {"retrieved_at": iso(datetime(2026, 11, 24, 21, 21)), "schedule": [{"game_id": 1, "completed": False}, {"game_id": 2, "completed": True}]}
    live_polls = {"poll_weeks": {"ap_top25": 13, "coaches_top25": 13}, "cfp_published_at": "2026-11-17", "cfp_week": 12}
    runs = {"event-watcher.yml": [{"id": 9, "status": "in_progress", "event": "workflow_dispatch", "created_at": iso(now), "updated_at": iso(now)}],
            "dashboard.yml": [{"id": 5, "status": "completed", "conclusion": "success", "head_branch": "main", "created_at": iso(now - timedelta(hours=1))}]}
    args = dict(runs=runs, crons={}, snapshot=snapshot, live_report=live_report, live_polls=live_polls, official_cfp_exists=False)
    args.update(over)
    return args


def test_monitor_reports_the_24_november_failure_modes():
    now = datetime(2026, 11, 25, 1, 30, tzinfo=timezone.utc)
    # The incident: official page out since ~18:00 Central, site still on 17 November; poll crons silent.
    a = fm.assess(now, **_state(now, official_cfp_exists=True,
                                crons={"refresh-polls.yml": ["*/15 23 * 11-12 2", "*/15 0-5 * 11-12 3"]},
                                runs={"refresh-polls.yml": [{"event": "schedule", "created_at": "2026-11-24T02:49:21Z"}]}))
    keys = {x["key"]: x for x in a}
    assert keys["cfp-unpublished:2026-11-24"]["severity"] == "critical"
    assert "missed-schedule:refresh-polls.yml" in keys and "watcher-stopped" in keys
    # Game 1 (kickoff 18:00 UTC) is past its latest finish but the site still shows it incomplete.
    assert keys["games-awaiting"]["area"] == "Scores and records"
    # Everything fine: no alerts.
    ok_state = _state(now)
    ok_state["live_polls"] = {**ok_state["live_polls"], "cfp_published_at": "2026-11-24", "cfp_week": 13}
    ok_state["live_report"] = {**ok_state["live_report"], "retrieved_at": iso(now), "schedule": [{"game_id": 1, "completed": True}, {"game_id": 2, "completed": True}]}
    assert fm.assess(now, **ok_state) == []


def test_monitor_failed_deploy_quota_and_overdue_poll():
    now = datetime(2026, 11, 23, 22, 0, tzinfo=timezone.utc)          # Monday afternoon: poll overdue if behind
    state = _state(now)
    state["runs"]["dashboard.yml"] = [
        {"id": 7, "status": "completed", "conclusion": "failure", "head_branch": "main", "created_at": iso(now - timedelta(minutes=10)), "html_url": "u"},
        {"id": 6, "status": "completed", "conclusion": "success", "head_branch": "main", "created_at": iso(now - timedelta(hours=2))}]
    state["live_polls"] = {**state["live_polls"], "poll_weeks": {"ap_top25": 12, "coaches_top25": 13}}
    a = {x["key"] for x in fm.assess(now, **state, quota={"remaining": 30, "spendable": 0, "days_to_reset": 8})}
    assert {"deploy-failed", "poll-overdue:ap_top25:13", "quota-discretionary"} <= a
    # A failure superseded by a later successful deployment is not an alert.
    state["runs"]["dashboard.yml"].insert(0, {"id": 8, "status": "completed", "conclusion": "success", "head_branch": "main", "created_at": iso(now)})
    assert "deploy-failed" not in {x["key"] for x in fm.assess(now, **state)}
    assert "quota-floor" in {x["key"] for x in fm.assess(now, **state, quota={"remaining": 5, "spendable": 0})}


def test_alert_issue_opens_updates_only_on_change_and_closes():
    issues, comments = {}, []

    def github(path, method="GET", body=None):
        if path.startswith("issues?"):
            return [i for i in issues.values() if i["state"] == "open"]
        if path == "issues" and method == "POST":
            n = len(issues) + 1
            issues[n] = {"number": n, "title": body["title"], "body": body["body"], "state": "open"}
            return issues[n]
        if path.endswith("/comments"):
            comments.append(body["body"])
            return {}
        n = int(path.split("/")[1])
        issues[n].update({k: v for k, v in body.items() if k in ("body", "state")})
        return issues[n]

    now = TUESDAY
    one = [fm._alert("cfp-unpublished:2026-11-24", "CFP rankings", "critical", "out but not published")]
    assert fm.sync_issue(github, one, now, log=lambda *_: None) == "opened"
    assert fm.sync_issue(github, one, now, log=lambda *_: None) == "unchanged" and not comments
    two = one + [fm._alert("watcher-stopped", "Live monitoring", "critical", "no watcher")]
    assert fm.sync_issue(github, two, now, log=lambda *_: None) == "updated" and len(comments) == 1
    assert fm.keys_of(issues[1]["body"]) == sorted(a["key"] for a in two)       # machine-readable block for the site
    assert fm.sync_issue(github, [], now, log=lambda *_: None) == "closed" and issues[1]["state"] == "closed"
    assert fm.sync_issue(github, [], now, log=lambda *_: None) == "clear"


def test_scheduled_poll_runs_skip_cfbd_unless_a_poll_can_change():
    games = {"games": [game(1, datetime(2026, 11, 21, 17, 0, tzinfo=timezone.utc), True, 1, 0, week=12)]}
    current = {"poll_weeks": {"ap_top25": 13, "coaches_top25": 13}}
    behind = {"poll_weeks": {"ap_top25": 12, "coaches_top25": 13}}
    tuesday_evening = datetime(2026, 11, 25, 1, 0, tzinfo=timezone.utc)
    sunday = datetime(2026, 11, 22, 19, 0, tzinfo=timezone.utc)
    assert not poll_refresh.poll_check_needed(tuesday_evening, behind, games)      # not a poll day: no CFBD call
    assert not poll_refresh.poll_check_needed(sunday, current, games)
    assert poll_refresh.poll_check_needed(sunday, behind, games)


class MonitorProviders:
    """GitHub + live site for a full monitor pass (no CFBD)."""

    def __init__(self, now, watcher_runs, live_polls, official=True):
        self.now, self.dispatched, self.issues, self.comments = now, [], {}, []
        self.runs = {"event-watcher.yml": watcher_runs}
        self.polls, self.official = live_polls, official

    def workflow_runs(self, workflow, per_page=30):
        return self.runs.get(workflow, [])

    def live_report(self):
        return {"retrieved_at": iso(self.now), "schedule": []}

    def live_polls(self):
        return self.polls

    def cfp_page(self, url):
        return "<html>official</html>" if self.official else None

    def dispatch(self, workflow, inputs=None):
        self.dispatched.append(workflow)

    def github(self, path, method="GET", body=None):
        if path.startswith("issues?"):
            return [i for i in self.issues.values() if i["state"] == "open"]
        if path == "issues" and method == "POST":
            n = len(self.issues) + 1
            self.issues[n] = {"number": n, "title": body["title"], "body": body["body"], "state": "open"}
            return self.issues[n]
        if path.endswith("/comments"):
            self.comments.append(body["body"])
            return {}
        n = int(path.split("/")[1])
        self.issues[n].update({k: v for k, v in body.items() if k in ("body", "state")})
        return self.issues[n]


def test_monitor_pass_alerts_redeploys_the_status_and_the_site_status_reflects_it():
    now = datetime(2026, 11, 25, 1, 0, tzinfo=timezone.utc)
    snapshot = {"season": 2026, "games": [game(9, datetime(2026, 11, 28, 17, 0, tzinfo=timezone.utc), week=14)]}
    stopped = [{"id": 1, "status": "completed", "updated_at": iso(now - timedelta(hours=4)), "created_at": iso(now - timedelta(hours=10))}]
    p = MonitorProviders(now, stopped, {"poll_weeks": {"ap_top25": 13, "coaches_top25": 13}, "cfp_published_at": "2026-11-17", "cfp_week": 12})
    alerts = fm.run_pass(p, now=now, snapshot=snapshot, watcher_running=False, log=lambda *_: None, crons={})
    assert {"watcher-stopped", "cfp-unpublished:2026-11-24"} <= {a["key"] for a in alerts}
    assert p.dispatched == ["dashboard.yml"]                     # alerts changed -> republish monitor-status.json
    status = fm.site_status(p, now, snapshot)
    assert status["watcher"]["state"] == "stopped" and {a["key"] for a in status["alerts"]} >= {"watcher-stopped"}
    # A second identical pass changes nothing and does not redeploy.
    fm.run_pass(p, now=now, snapshot=snapshot, watcher_running=False, log=lambda *_: None, crons={})
    assert p.dispatched == ["dashboard.yml"]
    # Resolved: watcher running, release published -> issue closed, site redeployed, status active and clear.
    p.runs["event-watcher.yml"] = [{"id": 2, "status": "in_progress", "updated_at": iso(now), "created_at": iso(now)}]
    p.polls = {**p.polls, "cfp_published_at": "2026-11-24", "cfp_week": 13}
    assert fm.run_pass(p, now=now, snapshot=snapshot, watcher_running=True, log=lambda *_: None, crons={}) == []
    assert p.dispatched == ["dashboard.yml", "dashboard.yml"] and p.issues[1]["state"] == "closed"
    status = fm.site_status(p, now, snapshot)
    assert status["watcher"]["state"] == "active" and status["alerts"] == []
    # Season over: an ended chain is idle, not interrupted.
    p.runs["event-watcher.yml"] = stopped
    assert fm.site_status(p, now, {"season": 2026, "games": []})["watcher"]["state"] in ("idle", "stopped")


def test_watcher_and_keeper_passes_do_not_flip_the_issue_or_redeploy_on_warnings():
    """Production 25 November: the watcher pass (with a quota reading) added a quota warning, the keeper pass (without
    one) removed it, and every flip commented and redeployed. Callers now keep what they cannot evaluate, and only a
    change in critical alerts redeploys the site."""
    now = datetime(2026, 11, 25, 4, 0, tzinfo=timezone.utc)
    snapshot = {"season": 2026, "games": [game(9, datetime(2026, 11, 28, 17, 0, tzinfo=timezone.utc), week=14)]}
    running = [{"id": 2, "status": "in_progress", "updated_at": iso(now), "created_at": iso(now)}]
    p = MonitorProviders(now, running, {"poll_weeks": {"ap_top25": 13, "coaches_top25": 13}, "cfp_published_at": "2026-11-24", "cfp_week": 13})
    quota = {"remaining": 29, "spendable": 0, "days_to_reset": 6}
    quiet = lambda *_: None
    fm.run_pass(p, now=now, snapshot=snapshot, quota=quota, watcher_alerts=[], log=quiet, crons={})      # watcher
    assert p.issues[1]["state"] == "open" and fm.keys_of(p.issues[1]["body"]) == ["quota-discretionary"]
    comments = len(p.comments)
    for _ in range(3):
        fm.run_pass(p, now=now, snapshot=snapshot, log=quiet, crons={})                                   # keeper
        fm.run_pass(p, now=now, snapshot=snapshot, quota=quota, watcher_alerts=[], log=quiet, crons={})   # watcher
    assert fm.keys_of(p.issues[1]["body"]) == ["quota-discretionary"] and len(p.comments) == comments
    assert p.dispatched == []                                     # warnings never redeploy the site
    # The watcher, which can evaluate quota, clears it once the budget recovers; the issue closes.
    fm.run_pass(p, now=now, snapshot=snapshot, quota={"remaining": 900, "spendable": 300, "days_to_reset": 6}, watcher_alerts=[], log=quiet, crons={})
    assert p.issues[1]["state"] == "closed" and p.dispatched == []
