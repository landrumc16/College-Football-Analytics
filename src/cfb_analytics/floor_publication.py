"""Time-based essential publication while the CFBD quota sits at its protected floor (Nov 27 incident).

When the quota cannot fund detection checks, the watcher used to wait without publishing anything (0 CFBD calls
during the whole November 27 evening). This schedules essential-only refreshes after each kickoff cluster's latest
expected finish instead. Each costs one CFBD call (``skip_postseason``) at the ``publication`` level, which may
spend the floor. One call is kept for the official AP/Coaches release when a poll Sunday falls before the reset.
Every watcher run recomputes the plan from the live remaining quota, and a wave is skipped when another refresh ran
recently, so chained watcher runs cannot double-spend.
"""
from datetime import datetime, timedelta, timezone

from . import event_calendar as cal

POLL_PUBLISH_UTC = (20, 45)     # Sunday 14:45 CT: AP and Coaches polls are normally both out by then
RECENT_REFRESH = timedelta(minutes=45)
REFRESH_INPUTS = {'season': '2026', 'essential_only': 'true', 'skip_postseason': 'true'}


def _next_poll_sunday(now, reset):
    day = now.astimezone(timezone.utc).replace(hour=POLL_PUBLISH_UTC[0], minute=POLL_PUBLISH_UTC[1], second=0, microsecond=0)
    for offset in range(8):
        moment = day + timedelta(days=offset)
        if moment.weekday() == 6 and now <= moment + timedelta(hours=6) and moment < reset:
            return max(moment, now)
    return None


def plan(snapshot, now, remaining, reset, *, polls_published_for_sunday=False):
    """Events to publish before the reset, newest quota first: [(time, kind)] with kind 'games' or 'polls'."""
    poll_at = None if polls_published_for_sunday or remaining < 1 else _next_poll_sunday(now, reset)
    # Keep one spare call for a failed refresh's retry when the quota allows it.
    allowed = max(0, remaining - (1 if poll_at else 0) - (1 if remaining > 2 else 0))
    ends = {}
    for game in snapshot.get('games', []):
        kickoff = cal.parse_time(game.get('start_date'))
        if game.get('completed') or not kickoff:
            continue
        end = kickoff + cal.LATE_FINISH
        if end >= reset or now > end + cal.OVERDUE_LIMIT:
            continue
        cluster = (kickoff.date(), kickoff.hour)
        ends[cluster] = max(ends.get(cluster, end), end)
    times = sorted({max(end, now) for end in ends.values()})
    merged = []
    for moment in times:  # one refresh publishes every final so far: merge waves closer than an hour
        if merged and moment - merged[-1] < timedelta(hours=1):
            merged[-1] = moment
        else:
            merged.append(moment)
    if len(merged) > allowed:
        # Keep the last wave (it publishes everything) and spread the rest evenly before it.
        keep = [merged[-1]] if allowed else []
        if allowed > 1:
            step = (len(merged) - 1) / (allowed - 1)
            keep = sorted({merged[round(i * step)] for i in range(allowed - 1)} | {merged[-1]})
        merged = keep
    events = [(moment, 'games') for moment in merged]
    if poll_at:
        events.append((poll_at, 'polls'))
    return sorted(events)


class FloorPublisher:
    """Watcher component: dispatch the planned essential refreshes at their times, never twice."""

    def __init__(self, providers, clock, events, *, log=print):
        self.p, self.clock, self.log = providers, clock, log
        self.events = [{'at': at, 'kind': kind, 'status': 'planned'} for at, kind in events]
        self.alerts = []

    def pending(self):
        return [e for e in self.events if e['status'] == 'planned']

    def next_wait(self, now):
        upcoming = [e['at'] for e in self.pending()]
        return max(0.0, (min(upcoming) - now).total_seconds()) if upcoming else None

    def _recent(self, workflow, now, window, dispatch_only=False):
        for run in self.p.workflow_runs(workflow, 10):
            created = cal.parse_time(run.get('created_at'))
            if created and now - created < window and (not dispatch_only or run.get('event') == 'workflow_dispatch'):
                return True
        return False

    def step(self):
        now = self.clock()
        for event in self.pending():
            if event['at'] > now:
                continue
            try:
                if event['kind'] == 'games':
                    if self._recent('refresh-data.yml', now, RECENT_REFRESH):
                        event['status'] = 'skipped (recent refresh)'
                        continue
                    self.p.dispatch('refresh-data.yml', dict(REFRESH_INPUTS))
                else:
                    if self._recent('refresh-polls.yml', now, timedelta(hours=6), dispatch_only=True):
                        event['status'] = 'skipped (recent poll publication)'
                        continue
                    self.p.dispatch('refresh-polls.yml', {'publication': 'true'})
                event.update(status='dispatched', dispatched_at=now.isoformat())
                self.log(f"floor publication: dispatched {event['kind']} refresh planned for {event['at'].isoformat()}")
            except Exception as error:  # retried on the next step; never stops the watcher
                message = f"Floor publication dispatch failed: {str(error)[:160]}"
                if message not in self.alerts:
                    self.alerts.append(message)

    def record(self):
        return [{**e, 'at': e['at'].isoformat()} for e in self.events]


def utcnow():
    return datetime.now(timezone.utc)
