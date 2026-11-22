"""Event-driven refresh: calendar windows and the full watcher lifecycle (detect -> dispatch -> verify on the site).

A simulated clock and a fake site that "deploys" a few minutes after each dispatch let every scenario run the real
Watcher loop end to end. The integration check against the real providers is the `--dry-run` job in
.github/workflows/event-watcher.yml.
"""
from datetime import datetime, timedelta, timezone

import pytest

from cfb_analytics import event_calendar as cal
from cfb_analytics.event_watcher import Watcher, VERIFY_TIMEOUT

T0 = datetime(2026, 11, 21, 17, 0, tzinfo=timezone.utc)    # Saturday 11:00 Central
iso = lambda t: t.isoformat().replace("+00:00", ".000Z")


def game(gid, kickoff, completed=False, hs=None, as_=None, week=12):
    return {"game_id": gid, "week": week, "home": f"H{gid}", "away": f"A{gid}", "start_date": iso(kickoff),
            "completed": completed, "home_score": hs, "away_score": as_, "neutral_site": False}


class Clock:
    def __init__(self, t):
        self.t = t

    def __call__(self):
        return self.t

    def sleep(self, seconds):
        self.t += timedelta(seconds=seconds)


class FakeProviders:
    """CFBD + GitHub + live site. `finals` maps game_id -> (time it becomes final in CFBD, home, away)."""

    def __init__(self, clock, snapshot, deploy_minutes=6):
        self.clock, self.deploy = clock, timedelta(minutes=deploy_minutes)
        self.base = {g["game_id"]: dict(g) for g in snapshot["games"]}
        self.finals, self.corrections, self.reschedules = {}, {}, {}
        self.polls_at = {}                 # poll -> (time published in CFBD, week)
        self.cfp_at = None
        self.games_down = set()            # minute offsets when /games fails
        self.rankings_down = False
        self.dispatch_fail = 0
        self.dispatches, self.cfbd_calls = [], 0
        self.site_report = {"schedule": [dict(g) for g in snapshot["games"]]}
        self.site_polls = {"poll_weeks": {"ap_top25": 12, "coaches_top25": 12}}
        self.pending_deploys = []
        self.stale_final = set()           # game ids CFBD reports (wrongly) as not final

    def _state(self):
        now = self.clock()
        out = []
        for gid, g in self.base.items():
            row = {"id": gid, "homeTeam": g["home"], "awayTeam": g["away"], "season": 2026, "week": g["week"],
                   "startDate": self.reschedules.get(gid, g["start_date"]), "completed": g["completed"],
                   "homePoints": g["home_score"], "awayPoints": g["away_score"], "seasonType": "regular"}
            if gid in self.finals and now >= self.finals[gid][0]:
                row.update(completed=True, homePoints=self.finals[gid][1], awayPoints=self.finals[gid][2])
            if gid in self.corrections and now >= self.corrections[gid][0]:
                row.update(homePoints=self.corrections[gid][1], awayPoints=self.corrections[gid][2])
            if gid in self.stale_final:
                row.update(completed=False, homePoints=None, awayPoints=None)
            out.append(row)
        return out

    def games(self, season):
        self.cfbd_calls += 1
        if int((self.clock() - T0).total_seconds() // 60) in self.games_down or "all" in self.games_down:
            raise TimeoutError("CFBD timeout")
        return self._state()

    def rankings(self, season):
        self.cfbd_calls += 1
        if self.rankings_down:
            raise ConnectionError("rankings down")
        now, polls = self.clock(), []
        for name, key in (("AP Top 25", "ap_top25"), ("Coaches Poll", "coaches_top25")):
            at, week = self.polls_at.get(key, (None, None))
            if at and now >= at:
                polls.append((week, name))
        if self.cfp_at and now >= self.cfp_at[0]:
            polls.append((self.cfp_at[1], "Playoff Committee Rankings"))
        ranks = [{"rank": i, "school": f"T{i}"} for i in range(1, 26)]
        return [{"season": 2026, "week": w, "polls": [{"poll": n, "ranks": ranks}]} for w, n in polls]

    def dispatch(self, workflow, inputs=None):
        if self.dispatch_fail:
            self.dispatch_fail -= 1
            raise RuntimeError("GitHub 502")
        self.dispatches.append((self.clock(), workflow))
        self.pending_deploys.append((self.clock() + self.deploy, workflow, self._state()))

    def _apply_deploys(self):
        now = self.clock()
        for when, workflow, state in [d for d in self.pending_deploys if d[0] <= now]:
            self.pending_deploys.remove((when, workflow, state))
            if workflow == "refresh-data.yml":
                self.site_report = {"schedule": [{"game_id": r["id"], "completed": r["completed"], "home_score": r["homePoints"],
                                                  "away_score": r["awayPoints"]} for r in state]}
            else:
                for key, (at, week) in self.polls_at.items():
                    if at <= when:
                        self.site_polls["poll_weeks"][key] = week

    def live_report(self):
        self._apply_deploys()
        return self.site_report

    def live_polls(self):
        self._apply_deploys()
        return self.site_polls


def setup(games, polls=None, **kw):
    clock = Clock(kw.pop("start", T0))
    snapshot = {"season": 2026, "games": games}
    providers = FakeProviders(clock, snapshot, kw.pop("deploy_minutes", 6))
    w = Watcher(snapshot, polls or {"poll_weeks": {"ap_top25": 12, "coaches_top25": 12}, "cfp_week": 11}, providers,
                clock=clock, sleep=clock.sleep, active_interval=kw.pop("interval", 120), watch_interval=600, log=lambda *_: None)
    return clock, providers, w


def finals_of(w, kind="final"):
    return [e for e in w.events if e.kind == kind]


# ---- calendar ---------------------------------------------------------------------------------------------------
def test_calendar_windows_follow_kickoffs_and_never_assume_completion():
    k = T0
    g = game(1, k)
    assert cal.game_status(g, k - timedelta(minutes=1)) == "upcoming"
    assert cal.game_status(g, k + timedelta(hours=2)) == "in_progress"
    assert cal.game_status(g, k + timedelta(hours=3)) == "due"
    assert cal.game_status(g, k + timedelta(hours=6)) == "overdue"         # past the window: still monitored
    assert cal.game_status(g, k + timedelta(hours=50)) == "expired"        # daily baseline reconciles it
    assert cal.game_status(game(1, k, True, 1, 0), k + timedelta(hours=3)) == "final"
    quiet = cal.plan({"season": 2026, "games": [game(1, k + timedelta(days=2))]}, {}, k)
    assert quiet.intensity == "idle" and quiet.next_event_at == k + timedelta(days=2) + cal.EARLY_FINISH


def test_poll_and_cfp_windows():
    sunday = datetime(2026, 11, 22, 19, 0, tzinfo=timezone.utc)            # 13:00 Central
    snap = {"season": 2026, "games": [game(1, T0, True, 1, 0, week=12)]}
    p = cal.plan(snap, {"poll_weeks": {"ap_top25": 12, "coaches_top25": 13}}, sunday)
    assert p.polls_due == ["ap_top25"] and p.intensity == "active"         # week 13 AP expected; Coaches already out
    assert cal.poll_window(sunday + timedelta(hours=5)) == "overdue"        # late poll keeps being watched
    assert cal.cfp_window(datetime(2026, 11, 25, 0, 30, tzinfo=timezone.utc))      # Tue 24 Nov 18:30 Central
    assert not cal.cfp_window(datetime(2026, 11, 26, 0, 30, tzinfo=timezone.utc))


# ---- game lifecycle ---------------------------------------------------------------------------------------------
def test_simultaneous_finals_one_dispatch_then_verified_on_the_site_within_target():
    kick = T0 - timedelta(hours=3)
    clock, p, w = setup([game(1, kick), game(2, kick), game(3, kick)])
    for gid in (1, 2, 3):
        p.finals[gid] = (T0 + timedelta(minutes=10), 24 + gid, 17)
    result = w.run(T0 + timedelta(hours=3))
    assert len(p.dispatches) == 1 and p.dispatches[0][1] == "refresh-data.yml"
    assert [e.status for e in finals_of(w)] == ["published"] * 3
    lat = [e.record()["detection_to_publication_seconds"] for e in finals_of(w)]
    assert all(s <= 8 * 60 for s in lat), lat                            # 2-min checks + 6-min deploy
    assert result["latency"]["published"] == 3


def test_early_finish_overtime_and_delay():
    early, ot, delayed = game(1, T0 - timedelta(hours=2, minutes=20)), game(2, T0 - timedelta(hours=3)), game(3, T0 - timedelta(hours=1))
    clock, p, w = setup([early, ot, delayed])
    p.finals[1] = (T0, 35, 10)                                           # finished at 2h20 (early)
    p.finals[2] = (T0 + timedelta(hours=2, minutes=30), 27, 24)          # OT: final 5h30 after kickoff (overdue)
    p.reschedules[3] = iso(T0 + timedelta(hours=1))                      # weather delay: kickoff moved 2h later
    p.finals[3] = (T0 + timedelta(hours=4), 20, 13)
    w.run(T0 + timedelta(hours=6))
    assert {e.detail["game_id"]: e.status for e in finals_of(w)} == {1: "published", 2: "published", 3: "published"}
    assert any(e.kind == "reschedule" and e.detail["game_id"] == 3 for e in w.events)
    assert w.games[3]["start_date"] == iso(T0 + timedelta(hours=1))


def test_duplicate_detections_dispatch_once():
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))])
    p.finals[1] = (T0, 21, 14)
    for _ in range(5):
        w.step(); clock.sleep(120)
    assert len(p.dispatches) == 1 and len(finals_of(w)) == 1


def test_authoritative_correction_hours_later_propagates():
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))])
    p.finals[1] = (T0, 21, 14)
    p.corrections[1] = (T0 + timedelta(hours=2), 21, 17)                 # stat correction after the fast final
    w.run(T0 + timedelta(hours=5))
    assert [e.status for e in finals_of(w)] == ["published"]
    corr = finals_of(w, "correction")
    assert len(corr) == 1 and corr[0].detail["to"] == [21, 17] and corr[0].status == "published"
    assert len(p.dispatches) == 2


def test_stale_source_never_regresses_a_final_result():
    clock, p, w = setup([game(1, T0 - timedelta(hours=8), True, 30, 3), game(2, T0 - timedelta(hours=3))])
    p.stale_final.add(1)
    p.finals[2] = (T0, 10, 7)
    w.run(T0 + timedelta(hours=1))
    assert w.games[1]["completed"] and w.games[1]["home_score"] == 30
    assert any(s.get("game_id") == 1 for s in w.stale_signals)
    assert [e.detail["game_id"] for e in finals_of(w)] == [2]


def test_source_outage_backs_off_and_recovers():
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))])
    p.finals[1] = (T0, 14, 13)
    p.games_down = set(range(0, 15))                                     # CFBD down for 15 minutes
    w.run(T0 + timedelta(hours=2))
    assert w.health["games"].failures == 0                               # recovered
    assert [e.status for e in finals_of(w)] == ["published"]


def test_one_provider_failing_does_not_block_another():
    sunday = datetime(2026, 11, 22, 17, 30, tzinfo=timezone.utc)          # games overdue + AP window
    clock, p, w = setup([game(1, sunday - timedelta(hours=7), week=12)], start=sunday)
    p.finals[1] = (sunday + timedelta(minutes=5), 31, 28)
    p.rankings_down = True
    w.run(sunday + timedelta(hours=1))
    assert [e.status for e in finals_of(w)] == ["published"]
    assert w.health["rankings"].failures >= 1


def test_failed_dispatch_then_retry_and_failed_publication_redispatch():
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))])
    p.finals[1] = (T0, 7, 3)
    p.dispatch_fail = 2                                                   # GitHub API errors twice
    w.run(T0 + timedelta(hours=2))
    assert [e.status for e in finals_of(w)] == ["published"] and len(p.dispatches) == 1
    # A deploy that never shows the change is re-dispatched once, then alerted.
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))], deploy_minutes=10_000)
    p.finals[1] = (T0, 7, 3)
    w.run(T0 + timedelta(hours=2))
    assert len(p.dispatches) == 2 and finals_of(w)[0].status == "alerted" and w.alerts


def test_downtime_recovery_picks_up_yesterdays_overdue_finals():
    # The watcher was down overnight; at start the game is long past its window but still pending in the snapshot.
    start = T0 + timedelta(hours=14)
    clock, p, w = setup([game(1, T0)], start=start)
    p.finals[1] = (T0 + timedelta(hours=3), 28, 21)
    w.run(start + timedelta(minutes=30))
    assert [e.status for e in finals_of(w)] == ["published"]


def test_poll_published_late_and_cfp_release_is_alerted_not_published():
    sunday = datetime(2026, 11, 22, 17, 0, tzinfo=timezone.utc)
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=sunday)
    p.polls_at["coaches_top25"] = (sunday + timedelta(minutes=20), 13)    # earlier than AP
    p.polls_at["ap_top25"] = (sunday + timedelta(hours=6), 13)            # late: after the Sunday window (overdue)
    w.run(sunday + timedelta(hours=8))
    polls = {e.detail["poll"]: e.status for e in w.events if e.kind == "poll"}
    assert polls == {"coaches_top25": "published", "ap_top25": "published"}
    assert all(wf == "refresh-polls.yml" for _, wf in p.dispatches)
    tuesday = datetime(2026, 11, 24, 23, 30, tzinfo=timezone.utc)          # 17:30 Central CFP window
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=tuesday)
    p.cfp_at = (tuesday + timedelta(minutes=40), 13)
    w.run(tuesday + timedelta(hours=2))
    assert [e.status for e in w.events if e.kind == "cfp"] == ["alerted"] and not p.dispatches and w.alerts


def test_cfbd_call_budget_caps_a_long_day():
    clock, p, w = setup([game(i, T0 - timedelta(hours=2) + timedelta(minutes=10 * i)) for i in range(30)])
    w.cfbd_budget = 25
    w.run(T0 + timedelta(hours=6))
    assert p.cfbd_calls <= 25
