"""A new undated provider response must not discard a verified CFP publication."""
import copy
import io
import json
import pytest
from pathlib import Path
from cfb_analytics import poll_refresh

ROOT = Path(__file__).resolve().parents[1]


def current_week(snapshot):
    """The published poll week; tests are relative to it because routine poll refreshes advance it."""
    return snapshot['poll_weeks']['ap_top25']


@pytest.mark.parametrize("include_cfp", [True, False])
def test_live_poll_refresh_retains_last_independently_dated_cfp(tmp_path, monkeypatch, include_cfp):
    existing = json.loads((ROOT / 'data/poll-2026-snapshot.json').read_text())
    directory = tmp_path / 'data'
    directory.mkdir()
    target = directory / 'poll-2026-snapshot.json'
    target.write_text(json.dumps(existing))
    week = current_week(existing)
    response = [{'season': 2026, 'week': week, 'polls': [
        {'poll': label, 'ranks': [{'school': row['team'], 'rank': row['rank']} for row in existing[key]]}
        for label, key in [('AP', 'ap_top25'), ('Coaches Poll', 'coaches_top25'), ('CFP', 'cfp_top25')]]}]
    if not include_cfp:
        response[0]['polls'].pop()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('CFBD_API_KEY', 'test-only')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'workflow_dispatch')
    monkeypatch.setattr(poll_refresh, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(response).encode()))
    poll_refresh.main()
    updated = json.loads(target.read_text())
    assert updated['week'] == week
    for key in ('cfp_top25', 'cfp_published_at', 'cfp_week', 'cfp_source'):
        assert updated[key] == existing[key]


def test_undated_or_invalid_cfp_is_never_rehabilitated():
    existing = json.loads((ROOT / 'data/poll-2026-snapshot.json').read_text())
    for mutate in [lambda d: d.pop('cfp_published_at'),
                   lambda d: d.update(cfp_published_at='2026-12-31'),
                   lambda d: d['cfp_top25'].__setitem__(1, d['cfp_top25'][0]),
                   lambda d: d.update(cfp_source='')]:
        invalid = copy.deepcopy(existing)
        mutate(invalid)
        assert poll_refresh.retained_verified_cfp(invalid) == {}


def test_delayed_monday_ap_release_window():
    from datetime import datetime, timezone
    assert poll_refresh.release_window(datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc))
    assert not poll_refresh.release_window(datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc))


def test_lagging_provider_cannot_roll_back_the_verified_week(tmp_path, monkeypatch):
    existing = json.loads((ROOT / 'data/poll-2026-snapshot.json').read_text())
    week = current_week(existing)
    assert week >= 12 and existing['poll_weeks']['coaches_top25'] == week
    directory = tmp_path / 'data'
    directory.mkdir()
    target = directory / 'poll-2026-snapshot.json'
    target.write_text(json.dumps(existing))
    stale = [{'season': 2026, 'week': week - 1, 'polls': [
        {'poll': label, 'ranks': [{'school': row['team'], 'rank': row['rank']} for row in existing[key]]}
        for label, key in [('AP', 'ap_top25'), ('Coaches Poll', 'coaches_top25')]]}]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('CFBD_API_KEY', 'test-only')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'workflow_dispatch')
    monkeypatch.setattr(poll_refresh, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(stale).encode()))
    poll_refresh.main()
    assert json.loads(target.read_text()) == existing


def _run_with_provider(tmp_path, monkeypatch, existing, weeks):
    directory = tmp_path / 'data'
    directory.mkdir(exist_ok=True)
    target = directory / 'poll-2026-snapshot.json'
    target.write_text(json.dumps(existing))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('CFBD_API_KEY', 'test-only')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'workflow_dispatch')
    monkeypatch.setattr(poll_refresh, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(weeks).encode()))
    poll_refresh.main()
    return json.loads(target.read_text())


def _feed(existing, week, labels=(('AP', 'ap_top25'), ('Coaches Poll', 'coaches_top25'))):
    return [{'season': 2026, 'week': week, 'polls': [
        {'poll': label, 'ranks': [{'school': row['team'], 'rank': row['rank']} for row in existing[key]]}
        for label, key in labels]}]


def test_same_week_feed_keeps_verified_publication_dates(tmp_path, monkeypatch):
    existing = json.loads((ROOT / 'data/poll-2026-snapshot.json').read_text())
    assert _run_with_provider(tmp_path, monkeypatch, existing, _feed(existing, current_week(existing))) == existing


def test_delayed_ap_waits_then_publishes_both_with_retrieval_time(tmp_path, monkeypatch):
    existing = json.loads((ROOT / 'data/poll-2026-snapshot.json').read_text())
    week = current_week(existing)
    # Sunday: Coaches next week out, AP still on the current week -> wait, keep the verified snapshot.
    sunday = _feed(existing, week, (('AP', 'ap_top25'),)) + _feed(existing, week + 1, (('Coaches Poll', 'coaches_top25'),))
    assert _run_with_provider(tmp_path, monkeypatch, existing, sunday) == existing
    # Monday: delayed AP week 13 arrives -> both publish; no guessed publication dates; CFP kept.
    updated = _run_with_provider(tmp_path, monkeypatch, existing, _feed(existing, week + 1))
    assert updated['week'] == week + 1 and updated['poll_weeks'] == {'ap_top25': week + 1, 'coaches_top25': week + 1}
    assert 'ap_published_at' not in updated and 'coaches_published_at' not in updated
    assert updated['retrieved_at'].startswith('20')
    assert all(updated[k] == existing[k] for k in ('cfp_top25', 'cfp_published_at', 'cfp_week', 'cfp_source'))
