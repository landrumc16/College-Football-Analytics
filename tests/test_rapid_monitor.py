from datetime import datetime, timedelta, timezone
from pathlib import Path
from cfb_analytics.rapid_monitor import RapidInboxMonitor


class Provider:
    def __init__(self):
        self.calls = []; self.live = {}; self.registry = {'enabled': True, 'sources': {'https://licensed.example/finals': 'licensed'}}
        self.inbox = {'batch_id': 'batch-1', 'observations': [{'observation': {'source': 'https://licensed.example/finals'}}]}
    def live_fast_results(self): self.calls.append('live'); return self.live
    def rapid_inbox(self): self.calls.append('inbox'); return self.registry, self.inbox
    def dispatch(self, workflow, inputs): self.calls.append((workflow, inputs))


def setup(enabled=True):
    now = [datetime(2026, 11, 27, tzinfo=timezone.utc)]
    p = Provider(); m = RapidInboxMonitor(p, lambda: now[0], enabled=enabled)
    return now, p, m


def test_default_disabled_and_dry_run_do_not_read_or_dispatch():
    now, p, m = setup(False); m.step(); assert p.calls == []
    m.enabled = True; m.dry_run = True; m.step(); assert p.calls == []


def test_dispatch_does_not_acknowledge_publication_and_public_artifact_does():
    now, p, m = setup(); m.step()
    assert m.events[0]['status'] == 'dispatched'
    assert p.calls[-1] == ('refresh-data.yml', {'season': '2026', 'essential_only': 'true', 'rapid_only': 'true'})
    now[0] += timedelta(minutes=2); p.live = {'processed_batch_ids': ['batch-1']}; m.step()
    assert m.pending is None and m.events[0]['status'] == 'published'
    assert m.record()['events'][0]['published_at'] == now[0].isoformat()


def test_cross_session_public_batch_deduplication():
    now, p, m = setup(); p.live = {'processed_batch_ids': ['batch-1']}; m.step()
    assert not m.events and not any(isinstance(c, tuple) for c in p.calls)


def test_failed_publication_retries_once_then_alerts():
    now, p, m = setup(); m.step()
    for _ in range(3):
        now[0] += timedelta(minutes=21); m.step()
    assert m.pending['status'] == 'alerted' and m.pending['attempts'] == 2
    assert len([c for c in p.calls if isinstance(c, tuple)]) == 2
    assert m.alerts


def test_unlicensed_source_and_authoritative_spoof_are_refused():
    now, p, m = setup(); p.inbox['observations'][0]['authoritative'] = True; m.step()
    assert m.alerts and not m.events
    now, p, m = setup(); p.registry['sources'] = {}; m.step()
    assert m.alerts and not m.events


def test_workflow_shares_existing_lock_and_no_provider_credentials_in_rapid_job():
    workflow = Path('.github/workflows/refresh-data.yml').read_text()
    rapid = workflow.split('  rapid_publication:', 1)[1]
    assert 'group: cfb-2026-refresh' in workflow
    assert 'CFBD_API_KEY' not in rapid
    assert 'publish_refresh_snapshot.sh' in rapid
    assert '--cfbd-snapshot data/cfbd-2026-games.json' not in rapid
    assert "'--cfbd-snapshot', 'data/cfbd-2026-games.json'" in workflow
