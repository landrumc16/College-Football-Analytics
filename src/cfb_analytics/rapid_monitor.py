"""Optional inbox bridge for the existing watcher; never contacts a sports provider.

Only the trusted main-branch registry may enable an authorized adapter's inbox.
Publication is acknowledged from the public artifact, never a workflow exit code.
"""
from datetime import timedelta
import re


def valid_batch_id(value):
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value) is not None


class RapidInboxMonitor:
    def __init__(self, provider, clock, *, enabled=False, dry_run=False):
        self.provider, self.clock = provider, clock
        self.enabled, self.dry_run = enabled, dry_run
        self.next_check = None
        self.pending = None
        self.events = []
        self.alerts = []

    def step(self):
        if not self.enabled or self.dry_run:
            return
        now = self.clock()
        if self.next_check and now < self.next_check:
            return
        self.next_check = now + timedelta(seconds=120)
        try:
            live = self.provider.live_fast_results()
            published = set(live.get('processed_batch_ids', []))
            if self.pending:
                if self.pending['batch_id'] in published:
                    self.pending.update(status='published', published_at=now.isoformat())
                    self.pending = None
                elif now - self.pending['last_dispatch'] >= timedelta(minutes=20):
                    if self.pending['attempts'] >= 2:
                        self.pending['status'] = 'alerted'
                        message = 'Rapid results not publicly visible after two publication attempts'
                        if message not in self.alerts:
                            self.alerts.append(message)
                        self.pending = None
                    else:
                        self._dispatch(self.pending, now)
                if self.pending:
                    return
            excluded = published | {event['batch_id'] for event in self.events if event['status'] == 'alerted'}
            registry, inbox = self.provider.rapid_inbox(published=excluded)
            if registry.get('enabled') is not True:
                return
            if not inbox:
                return
            batch = inbox.get('batch_id')
            if not valid_batch_id(batch):
                raise ValueError('Rapid inbox requires immutable batch_id')
            if batch in published or any(e['batch_id'] == batch for e in self.events):
                return
            if not inbox.get('observations'):
                return
            # The publisher performs full identity/payload validation. The watcher
            # refuses disabled/unapproved sources and privileged CFBD attestations.
            from .ai_research import authorized_sources
            allowed = authorized_sources(registry, [e.get('observation', {}) for e in inbox['observations']])
            for envelope in inbox['observations']:
                source = envelope.get('observation', {}).get('source')
                if allowed.get(source) not in ('licensed', 'ai_research') or envelope.get('authoritative'):
                    raise ValueError('Rapid inbox source is not licensed or verified research, or attempts authoritative promotion')
            event = {'batch_id': batch, 'status': 'detected', 'detected_at': now.isoformat(), 'attempts': 0}
            self.events.append(event)
            self.pending = event
            self._dispatch(event, now)
        except Exception as error:
            message = 'Rapid inbox monitoring failed: ' + str(error)[:160]
            if message not in self.alerts:
                self.alerts.append(message)

    def _dispatch(self, event, now):
        event.update(status='dispatched', attempts=event['attempts'] + 1, last_dispatch=now)
        self.provider.dispatch('refresh-data.yml', {'season': '2026', 'essential_only': 'true', 'rapid_only': 'true', 'rapid_batch': event['batch_id']})

    def record(self):
        return {'events': [{k: (v.isoformat() if hasattr(v, 'isoformat') else v) for k, v in e.items()} for e in self.events],
                'alerts': self.alerts, 'enabled': self.enabled}
