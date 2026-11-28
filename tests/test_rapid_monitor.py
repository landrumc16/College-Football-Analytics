from datetime import datetime, timedelta, timezone
from pathlib import Path
from cfb_analytics.rapid_monitor import RapidInboxMonitor


class Provider:
    def __init__(self):
        self.calls = []; self.live = {}; self.registry = {'enabled': True, 'sources': {'https://licensed.example/finals': 'licensed'}}
        self.inbox = {'batch_id': 'batch-1', 'observations': [{'observation': {'source': 'https://licensed.example/finals'}}]}
    def live_fast_results(self): self.calls.append('live'); return self.live
    def rapid_inbox(self, published=()): self.calls.append('inbox'); return self.registry, self.inbox
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
    assert p.calls[-1] == ('refresh-data.yml', {'season': '2026', 'essential_only': 'true', 'rapid_only': 'true', 'rapid_batch': 'batch-1'})
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
    assert m.pending is None
    assert m.events[0]['status'] == 'alerted' and m.events[0]['attempts'] == 2
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


def test_queued_batch_pinned_when_pointer_advances_and_next_batch_detected():
    now, p, m = setup(); m.step()
    assert p.calls[-1][1]['rapid_batch'] == 'batch-1'
    p.inbox = dict(p.inbox, batch_id='batch-2')
    now[0] += timedelta(minutes=2)
    p.live = {'processed_batch_ids': ['batch-1']}
    m.step()
    assert m.events[0]['status'] == 'published'
    assert p.calls[-1][1]['rapid_batch'] == 'batch-2'


def test_batch_ids_refuse_path_traversal_and_shell_text():
    from cfb_analytics.rapid_monitor import valid_batch_id
    for value in ('../a', 'a/b', 'a.json', '$(echo x)', '', None, 'x'*129):
        assert not valid_batch_id(value)
    assert valid_batch_id('game-2026_abc')


def test_provider_fetches_pinned_immutable_batch(monkeypatch):
    from cfb_analytics import event_watcher as ew
    calls = []
    payloads = [{'enabled': True}, {'batch_ids': ['batch-1', 'batch-2']}, {'batch_id': 'batch-1', 'observations': []}]
    def fetch(url):
        calls.append(url); return payloads.pop(0)
    monkeypatch.setattr(ew, '_get_json', fetch)
    registry, inbox = ew.Providers('', '').rapid_inbox()
    assert calls[-1].endswith('/operations/rapid-inbox/batch-1.json')
    assert inbox['batch_id'] == 'batch-1'


def test_unobserved_older_batch_in_index_is_not_lost(monkeypatch):
    from cfb_analytics import event_watcher as ew
    def fetch(url):
        if url.endswith('rapid-sources.json'): return {'enabled': True}
        if url.endswith('rapid-inbox.json'): return {'batch_ids': ['batch-a', 'batch-b']}
        return {'batch_id': url.rsplit('/', 1)[1][:-5], 'observations': []}
    monkeypatch.setattr(ew, '_get_json', fetch)
    p = ew.Providers('', '')
    assert p.rapid_inbox(published=set())[1]['batch_id'] == 'batch-a'
    assert p.rapid_inbox(published={'batch-a'})[1]['batch_id'] == 'batch-b'
    assert p.rapid_inbox(published={'batch-a', 'batch-b'})[1] == {}


def test_independent_batches_survive_failed_publication():
    now, p, m = setup()
    batches = [dict(p.inbox, batch_id='batch-a'), dict(p.inbox, batch_id='batch-b')]
    p.rapid_inbox = lambda published=(): (p.registry, next((b for b in batches if b['batch_id'] not in published), {}))
    m.step()
    assert m.pending['batch_id'] == 'batch-a'
    for _ in range(2):
        now[0] += timedelta(minutes=21); m.step()
    assert m.events[0]['status'] == 'alerted'
    assert m.pending['batch_id'] == 'batch-b'
    p.live = {'processed_batch_ids': ['batch-b']}
    now[0] += timedelta(minutes=2); m.step()
    assert m.pending is None
    assert m.events[1]['status'] == 'published'


def test_two_indexed_batches_both_independently_publish():
    now, p, m = setup()
    batches = [dict(p.inbox, batch_id='batch-a'), dict(p.inbox, batch_id='batch-b')]
    p.rapid_inbox = lambda published=(): (p.registry, next((b for b in batches if b['batch_id'] not in published), {}))
    m.step()
    for published in (['batch-a'], ['batch-a', 'batch-b']):
        p.live = {'processed_batch_ids': published}
        now[0] += timedelta(minutes=2); m.step()
    assert [e['status'] for e in m.events] == ['published', 'published']
    assert [c[1]['rapid_batch'] for c in p.calls if isinstance(c, tuple)] == ['batch-a', 'batch-b']
