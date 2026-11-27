import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import pytest
from cfb_analytics.quota_client import reserve, coordinate, priority, QuotaUnavailable

NOW = datetime(2026, 11, 27, 15, tzinfo=timezone.utc)
INFO = {'remainingCalls': 14, 'resetAt': '2026-12-01T00:00:00Z'}


class Ledger:
    def __init__(self):
        self.state, self.version = None, 0
        self.lock = threading.Lock()

    def read(self):
        with self.lock:
            return self.state, self.version

    def write(self, state, sha):
        with self.lock:
            if sha != self.version:
                return False
            self.state = state
            self.version += 1
            return True


def test_concurrent_workflows_cannot_spend_the_same_reserved_capacity():
    ledger = Ledger()
    def request(i):
        try:
            coordinate(ledger, INFO, str(i), 8, 'essential', NOW)
            return True
        except QuotaUnavailable:
            return False
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(request, range(12)))
    assert sum(results) == 6
    assert ledger.state['remaining'] == 8
    assert sum(r['attempts'] for r in ledger.state['runs'].values()) == 6


def test_cap_survives_process_restart_and_failed_source_attempt():
    state = reserve(None, INFO, 'same-run', 2, 'essential', NOW)
    state = reserve(state, INFO, 'same-run', 2, 'essential', NOW)
    with pytest.raises(QuotaUnavailable):
        reserve(state, INFO, 'same-run', 2, 'essential', NOW)


def test_core_and_supplemental_leave_distinct_essential_reserves():
    info = {**INFO, 'remainingCalls': 22}
    with pytest.raises(QuotaUnavailable):
        reserve(None, info, 'supp', 8, 'supplemental', NOW)
    assert reserve(None, info, 'core', 7, 'core', NOW)['remaining'] == 21
    assert reserve(None, INFO, 'essential', 8, 'essential', NOW)['remaining'] == 13


def test_provider_read_cannot_erase_in_flight_or_crashed_reservations():
    state = reserve(None, INFO, 'one', 8, 'essential', NOW)
    assert reserve(state, INFO, 'two', 8, 'essential', NOW)['remaining'] == 12
    assert reserve(state, {**INFO, 'remainingCalls': 10}, 'two', 8, 'essential', NOW)['remaining'] == 9


def test_monthly_reset_starts_a_new_budget_only_from_current_provider_evidence():
    old = reserve(None, INFO, 'one', 8, 'essential', NOW)
    now = datetime(2026, 12, 1, 1, tzinfo=timezone.utc)
    info = {'remainingCalls': 1000, 'resetAt': '2027-01-01T00:00:00Z'}
    assert reserve(old, info, 'one', 8, 'essential', now)['remaining'] == 999
    with pytest.raises(QuotaUnavailable):
        reserve(old, INFO, 'one', 8, 'essential', now)


def test_batched_endpoints_are_essential_but_historical_retrieval_is_not():
    for endpoint in ['games', 'rankings']:
        assert priority(f'https://api.collegefootballdata.com/{endpoint}?year=2026', 2026) == 'essential'
        assert priority(f'https://api.collegefootballdata.com/{endpoint}?year=2025', 2026) == 'supplemental'
    assert priority('https://api.collegefootballdata.com/plays?year=2026', 2026) == 'core'
    assert priority('https://api.collegefootballdata.com/lines?year=2026', 2026) == 'supplemental'


def test_real_adapter_reserves_failed_attempt_and_blocks_retry_before_source(monkeypatch):
    import io
    from urllib.error import HTTPError
    from urllib.request import Request
    from cfb_analytics import quota_client as q
    ledger = Ledger()
    for key, value in {'GITHUB_ACTIONS': 'true', 'CFBD_API_KEY': 'test', 'GITHUB_TOKEN': 'test',
                       'GITHUB_REPOSITORY': 'owner/repo', 'GITHUB_RUN_ID': '123',
                       'CFBD_SHARED_QUOTA': 'github', 'CFBD_ACQUISITION_LIMIT': '1'}.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(q, 'GitHubLedger', lambda *args: ledger)
    sent = []
    def network(req, **kwargs):
        if req.full_url.endswith('/info'):
            return io.BytesIO(b'{"remainingCalls":100,"resetAt":"2099-01-01T00:00:00Z"}')
        sent.append(req.full_url)
        raise HTTPError(req.full_url, 503, 'provider unavailable', {}, None)
    monkeypatch.setattr(q, 'network_open', network)
    request = Request('https://api.collegefootballdata.com/games?year=2026')
    with pytest.raises(HTTPError):
        q.urlopen(request)
    with pytest.raises(QuotaUnavailable):
        q.urlopen(request)
    assert len(sent) == 1 and ledger.state['runs']['123']['attempts'] == 1


def test_missing_broker_setup_fails_closed_before_any_network(monkeypatch):
    from cfb_analytics import quota_client as q
    monkeypatch.setenv('GITHUB_ACTIONS', 'true')
    monkeypatch.setenv('CFBD_API_KEY', 'test')
    monkeypatch.delenv('CFBD_SHARED_QUOTA', raising=False)
    monkeypatch.setattr(q, 'network_open', lambda *a, **kw: pytest.fail('Unreserved request'))
    with pytest.raises(QuotaUnavailable):
        q.urlopen('https://api.collegefootballdata.com/rankings?year=2026')


def test_essential_dispatch_excludes_supplemental_acquisition():
    from test_event_driven import setup, game, T0
    from datetime import timedelta
    clock, providers, watcher = setup([game(1, T0 - timedelta(hours=3))])
    providers.finals[1] = (T0, 48, 27)
    seen = []
    dispatch = providers.dispatch
    def recording(workflow, inputs=None):
        seen.append((workflow, inputs))
        dispatch(workflow, inputs)
    providers.dispatch = recording
    watcher.run(T0 + timedelta(minutes=15))
    assert seen == [('refresh-data.yml', {'season': '2026', 'essential_only': 'true'})]


def test_capacity_model_does_not_claim_measurements_or_a_free_two_minute_season():
    from scripts.acquisition_capacity import report
    r = report()
    assert r['source_calls_made'] == 0 and r['kind'] == 'scenario_estimate_not_measurement'
    assert r['ordinary_four_week_month']['two_minute_total'] > r['free_monthly_limit']
    assert r['scenarios']['conference_championships']['two_minute_checks']['status_checks'] == 480


def test_unknown_first_availability_cannot_be_counted_as_a_five_minute_success():
    from test_event_driven import setup, game, T0
    from datetime import timedelta
    clock, providers, watcher = setup([game(1, T0 - timedelta(hours=3))], deploy_minutes=3)
    providers.finals[1] = (T0, 48, 27)
    result = watcher.run(T0 + timedelta(minutes=15))
    event, = result['events']
    assert event['published_at'] and event['availability_evidence'] == 'unknown'
    assert event['authoritative_first_available_at'] is None and event['total_seconds_at_most'] is None
    assert result['latency']['published_without_availability_bound'] == 1
    assert result['latency']['within_5_minutes_total'] == 0
    assert result['latency']['target_verified'] is False


def test_batched_snapshot_adds_new_fbs_events_to_the_existing_calendar():
    from test_event_driven import setup, game, T0
    from datetime import timedelta
    clock, providers, watcher = setup([game(1, T0 - timedelta(hours=3))])
    watcher.monitored_teams = {'H1', 'H2'}
    providers.base[2] = game(2, T0 + timedelta(hours=2))
    providers.base[3] = game(3, T0 + timedelta(hours=2))  # no FBS participant
    watcher.check_games()
    assert 2 in watcher.games and 3 not in watcher.games
    assert any(g['game_id'] == 2 for g in watcher.snapshot['games'])
    assert providers.cfbd_calls == 1  # one batch covers existing and new games


def test_equivalent_reset_timestamp_does_not_erase_existing_reservations():
    state = reserve(None, INFO, 'one', 8, 'essential', NOW)
    info = {**INFO, 'resetAt': '2026-12-01T00:00:00+00:00'}
    assert reserve(state, info, 'two', 8, 'essential', NOW)['remaining'] == 12
