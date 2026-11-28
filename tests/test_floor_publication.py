"""Time-based essential publication at the protected CFBD floor (November 27 incident)."""
from datetime import datetime, timedelta, timezone
from cfb_analytics import floor_publication as fp

RESET = datetime(2026, 12, 1, tzinfo=timezone.utc)
SAT = datetime(2026, 11, 28, 13, 30, tzinfo=timezone.utc)


def game(gid, kickoff, completed=False):
    return {'game_id': gid, 'start_date': kickoff.isoformat().replace('+00:00', 'Z'), 'completed': completed}


def saturday_slate():
    k = lambda h, m=0, d=28: datetime(2026, 11, d, h, m, tzinfo=timezone.utc)
    games = [game(1, k(0, 30)), game(2, k(17)), game(3, k(17, 30)), game(4, k(19)), game(5, k(20, 30)),
             game(6, k(0, 30, 29)), game(7, k(2, 30, 29)), game(8, k(4, 0, 29)), game(9, k(17, d=27), completed=True)]
    return {'games': games}


def test_overdue_and_today_windows_are_published_with_a_poll_reserve():
    events = fp.plan(saturday_slate(), SAT, 8, RESET)
    kinds = [k for _, k in events]
    assert kinds.count('polls') == 1 and kinds.count('games') <= 7
    first = events[0]
    assert first == (SAT, 'games')                                   # overdue Friday-night game: publish now
    polls = next(t for t, k in events if k == 'polls')
    assert polls == datetime(2026, 11, 29, 20, 45, tzinfo=timezone.utc)
    last_game = max(t for t, k in events if k == 'games')
    assert last_game == datetime(2026, 11, 29, 4, tzinfo=timezone.utc) + fp.cal.LATE_FINISH  # Hawai'i window


def test_quota_at_9_8_7_1_0_never_plans_more_than_it_can_spend():
    for remaining in (9, 8, 7, 1, 0):
        events = fp.plan(saturday_slate(), SAT, remaining, RESET)
        assert len(events) <= remaining                               # one CFBD call per planned refresh
        games = [t for t, k in events if k == 'games']
        assert len(games) <= max(0, remaining - 1 - (1 if remaining > 2 else 0))   # poll reserve and a retry spare
        if remaining >= 2:
            assert games[-1] == datetime(2026, 11, 29, 4, tzinfo=timezone.utc) + fp.cal.LATE_FINISH
    assert fp.plan(saturday_slate(), SAT, 0, RESET) == []
    assert fp.plan(saturday_slate(), SAT, 1, RESET) == [(datetime(2026, 11, 29, 20, 45, tzinfo=timezone.utc), 'polls')]


def test_nothing_is_planned_after_the_reset_or_for_completed_games():
    late = datetime(2026, 11, 30, 23, tzinfo=timezone.utc)
    assert fp.plan({'games': [game(1, late), game(2, SAT - timedelta(hours=3), completed=True)]}, SAT, 5, RESET) \
        == [(datetime(2026, 11, 29, 20, 45, tzinfo=timezone.utc), 'polls')]


class Providers:
    def __init__(self, runs=()):
        self.runs, self.sent = list(runs), []
    def workflow_runs(self, workflow, per_page=30):
        return [r for r in self.runs if r['workflow'] == workflow]
    def dispatch(self, workflow, inputs=None):
        self.sent.append((workflow, inputs))


def test_publisher_dispatches_essential_only_refreshes_once_and_skips_after_a_recent_refresh():
    now = [SAT]
    p = Providers()
    pub = fp.FloorPublisher(p, lambda: now[0], [(SAT, 'games'), (SAT + timedelta(hours=7), 'games'),
                                                 (SAT + timedelta(hours=31), 'polls')], log=lambda *a: None)
    pub.step()
    assert p.sent == [('refresh-data.yml', {'season': '2026', 'essential_only': 'true', 'skip_postseason': 'true'})]
    pub.step()
    assert len(p.sent) == 1                                          # never twice
    now[0] += timedelta(hours=7)
    p.runs.append({'workflow': 'refresh-data.yml', 'created_at': (now[0] - timedelta(minutes=10)).isoformat(), 'event': 'workflow_dispatch'})
    pub.step()
    assert len(p.sent) == 1 and pub.events[1]['status'].startswith('skipped')   # another refresh already ran
    now[0] += timedelta(hours=24)
    pub.step()
    assert p.sent[-1] == ('refresh-polls.yml', {'publication': 'true'}) and not pub.pending()


def test_dispatch_failures_are_retried_and_reported_without_stopping():
    p = Providers()
    calls = []
    def failing(workflow, inputs=None):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError('GitHub API 502')
        p.sent.append((workflow, inputs))
    p.dispatch = failing
    pub = fp.FloorPublisher(p, lambda: SAT, [(SAT, 'games')], log=lambda *a: None)
    pub.step()
    assert pub.alerts and pub.pending()
    pub.step()
    assert len(p.sent) == 1 and not pub.pending()


def test_poll_workflow_spends_the_floor_only_for_a_planned_publication():
    from pathlib import Path
    poll = Path('.github/workflows/refresh-polls.yml').read_text()
    assert "CFBD_ACQUISITION_ROLE: ${{ inputs.publication == true && 'publication' || 'detection' }}" in poll
    assert poll.count('CFBD_ACQUISITION_ROLE') == 1                  # the 15-minute cron checks stay at detection


def test_watcher_with_no_cfbd_budget_still_publishes_on_the_calendar():
    """The Nov 27 evening: zero detection budget. The watcher must dispatch the planned refreshes, spend no CFBD call."""
    from test_event_driven import setup, game as wgame, T0
    late = T0 - timedelta(hours=3)
    clock, providers, w = setup([wgame(1, late), wgame(2, T0 + timedelta(hours=1))], budget=0)
    events = fp.plan(w.snapshot, T0, 4, RESET)
    w.floor = fp.FloorPublisher(providers, clock, events, log=lambda *a: None)
    providers.workflow_runs = lambda workflow, per_page=30: []
    w.run(T0 + timedelta(hours=7))
    record = w.report()['floor_publication']
    assert [e['status'] for e in record if e['kind'] == 'games'] == ['dispatched', 'dispatched']
    assert providers.cfbd_calls == 0
    assert [when for when, wf in providers.dispatches if wf == 'refresh-data.yml'] == [t for t, k in events if k == 'games']
