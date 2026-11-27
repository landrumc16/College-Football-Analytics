"""Quota-pressure regression for the November 26 Texas Tech/TCU incident."""
from datetime import datetime, timedelta, timezone
import pytest

from test_event_driven import T0, game, setup
from cfb_analytics import event_calendar as cal
from cfb_analytics import event_watcher as ew


def signal_setup(final_after=timedelta(hours=3)):
    clock, p, w = setup([game(1, T0)], start=T0, budget=0, release_budget=7, deploy_minutes=3)
    w.wave_at = T0 + cal.LATE_FINISH
    p.final_signals = lambda games: {1} if clock() >= T0 + final_after else set()
    return clock, p, w


def test_actual_final_wakes_priority_refresh_before_end_of_day():
    clock, p, w = signal_setup()
    p.finals[1] = (T0 + timedelta(hours=3), 48, 27)
    w.run(T0 + timedelta(hours=5))
    e, = [e for e in w.events if e.kind == "final"]
    assert e.status == "published" and e.source == "cfbd/games" and e.priority
    assert e.detected_at <= T0 + timedelta(hours=3, minutes=2)
    assert p.cfbd_calls == 1 and w.release_spent == 5
    assert e.published_at < w.wave_at


def test_signal_never_supplies_a_score_and_provider_lag_is_bounded():
    clock, p, w = signal_setup()
    w.run(T0 + timedelta(hours=5))  # ESPN final; CFBD still incomplete
    assert not p.dispatches and not w.events
    assert p.cfbd_calls == 3 and w.release_spent == 3
    assert any("awaiting CFBD" in a for a in w.alerts)


def test_delayed_cfbd_confirmation_recovers_without_waiting_for_late_finish():
    clock, p, w = signal_setup()
    p.finals[1] = (T0 + timedelta(hours=3, minutes=3), 48, 27)
    w.run(T0 + timedelta(hours=5))
    e, = [e for e in w.events if e.kind == "final"]
    assert e.status == "published" and p.cfbd_calls == 2 and w.release_spent == 6


def test_failed_cfbd_requests_count_against_priority_cap():
    clock, p, w = signal_setup()
    p.games_down = {"all"}
    w.run(T0 + timedelta(hours=5))
    assert p.cfbd_calls <= 3 and w.release_spent == p.cfbd_calls
    assert not p.dispatches


def test_free_source_failure_keeps_timed_fallback():
    clock, p, w = signal_setup()
    def unavailable(games):
        raise TimeoutError("unavailable")
    p.final_signals = unavailable
    p.finals[1] = (T0 + timedelta(hours=3), 48, 27)
    w.run(T0 + timedelta(hours=5))
    e, = [e for e in w.events if e.kind == "final"]
    assert e.status == "published" and e.detected_at >= w.wave_at
    assert p.cfbd_calls == 1


def test_no_refresh_reserve_means_no_paid_calls():
    clock, p, w = signal_setup()
    w.release_budget = 4
    w.run(T0 + timedelta(hours=5))
    assert p.cfbd_calls == 0 and not p.dispatches
    assert any("reserve is unavailable" in a for a in w.alerts)


def test_late_start_still_funds_authoritative_confirmation_above_floor():
    now = T0 + timedelta(hours=5)
    snapshot = {"season": 2026, "games": [game(1, T0)]}
    q = ew.quota_plan({"remainingCalls": 20, "resetAt": "2026-12-01T00:00:00Z"}, snapshot, now)
    assert q["budget"] == 0 and q["priority_budget"] == 11
    assert cal.parse_time(q["wave_at"]) == now
    q = ew.quota_plan({"remainingCalls": 8, "resetAt": "2026-12-01T00:00:00Z"}, snapshot, now)
    assert q["priority_budget"] == 0


def test_tomorrows_games_cannot_postpone_todays_fallback():
    snapshot = {"season": 2026, "games": [game(1, T0), game(2, T0 + timedelta(hours=20))]}
    q = ew.quota_plan({"remainingCalls": 20, "resetAt": "2026-12-01T00:00:00Z"}, snapshot, T0)
    assert cal.parse_time(q["wave_at"]) == T0 + cal.LATE_FINISH


def test_actual_final_without_confirmation_is_a_critical_monitor_alert():
    from cfb_analytics.freshness_monitor import assess
    alerts = assess(T0, runs={}, crons={}, snapshot={"season": 2026, "games": []},
                    watcher_alerts=["ESPN reports a final awaiting CFBD confirmation; no secondary-source score was published"])
    assert any(a["severity"] == "critical" and "ESPN reports" in a["text"] for a in alerts)


@pytest.mark.parametrize("day", [26, 27, 28], ids=["Thursday", "Friday", "Saturday"])
def test_weekday_finals_receive_the_same_priority_latency_and_quota_protection(day):
    kickoff = datetime(2026, 11, day, 23, tzinfo=timezone.utc)
    snapshot = {"season": 2026, "games": [game(1, kickoff), game(2, kickoff + timedelta(hours=20))]}
    q = ew.quota_plan({"remainingCalls": 20, "resetAt": "2026-12-01T00:00:00Z"}, snapshot, kickoff)
    clock, p, w = setup(snapshot["games"], start=kickoff, budget=q["budget"],
                        release_budget=q["priority_budget"], deploy_minutes=3)
    w.wave_at = cal.parse_time(q["wave_at"])
    final = kickoff + timedelta(hours=3, minutes=30)
    p.finals[1] = (final, 48, 27)
    p.final_signals = lambda games: {1} if clock() >= final else set()
    w.run(kickoff + timedelta(hours=5))
    e, = [e for e in w.events if e.kind == "final"]
    assert e.status == "published" and e.published_at - final <= timedelta(minutes=5)
    assert w.release_spent == 5 and w.release_spent <= q["priority_budget"] <= 20 - ew.RELEASE_FLOOR
    assert w.wave_at == kickoff + cal.LATE_FINISH


def test_observed_final_forces_immediate_monitor_pass_instead_of_ten_minute_wait():
    clock, p, w = signal_setup()
    reported = []
    w.monitor = lambda watcher: reported.append((clock(), list(watcher.alerts)))
    clock.t = T0 + timedelta(hours=3, minutes=1)
    w._last_monitor = clock.t - timedelta(minutes=1)
    w.step()
    assert reported and reported[-1][0] == clock()
    assert any("awaiting CFBD" in a for a in reported[-1][1])


@pytest.mark.parametrize("priority", [False, True])
def test_failed_publication_cannot_spend_an_unfunded_retry(priority):
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))], budget=0 if priority else 5,
                        release_budget=5 if priority else 0, deploy_minutes=10000)
    if priority:
        w.wave_at = T0
    p.finals[1] = (T0, 48, 27)
    w.run(T0 + timedelta(hours=2))
    assert len(p.dispatches) == 1 and w.spent == 5
    assert w.events[0].status == "alerted" and any("quota exhausted" in a for a in w.alerts)


def test_funded_failed_publication_recovers_once_within_priority_cap():
    clock, p, w = setup([game(1, T0 - timedelta(hours=3))], budget=0, release_budget=11, deploy_minutes=3)
    w.wave_at = T0
    p.finals[1] = (T0, 48, 27)
    dispatch = p.dispatch
    def fail_first_publication(workflow, inputs=None):
        dispatch(workflow, inputs)
        if len(p.dispatches) == 1:
            p.pending_deploys.clear()  # workflow failed before publication; next fresh dispatch succeeds
    p.dispatch = fail_first_publication
    w.run(T0 + timedelta(hours=1))
    assert w.events[0].status == "published" and len(p.dispatches) == 2
    assert w.release_spent == 9 <= w.release_budget


def test_game_retry_guard_preserves_existing_discretionary_cfp_publication():
    from test_freshness_reliability import TUESDAY, RELEASED
    clock, p, w = setup([game(1, T0, True, 1, 0, week=12)], start=TUESDAY,
                        budget=400, release_budget=0)
    p.official_at, p.cfp_at = RELEASED, (RELEASED, 13)
    w.run(TUESDAY + timedelta(hours=2))
    assert [e.status for e in w.events if e.kind == "cfp"] == ["published"]


def test_scoreboard_requires_known_id_kickoff_complete_valid_score(monkeypatch):
    event = {"id": "1", "date": game(1, T0)["start_date"], "competitions": [{
        "status": {"type": {"completed": True}}, "competitors": [
            {"homeAway": "home", "score": "48"}, {"homeAway": "away", "score": "27"}]}]}
    monkeypatch.setattr(ew, "_get_json", lambda *a, **kw: {"events": [event]})
    p = ew.Providers("", "")
    assert p.final_signals([game(1, T0)]) == {1} and p.cfbd_calls == 0
    assert not p.final_signals([game(2, T0)])
    assert not p.final_signals([game(1, T0 + timedelta(hours=1))])
    event["competitions"][0]["status"]["type"]["completed"] = False
    assert not p.final_signals([game(1, T0)])
    event["competitions"][0]["status"]["type"]["completed"] = True
    event["competitions"][0]["competitors"][0]["score"] = "unknown"
    assert not p.final_signals([game(1, T0)])
