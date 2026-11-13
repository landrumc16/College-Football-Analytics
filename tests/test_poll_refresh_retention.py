"""A new undated provider response must not discard a verified CFP publication."""
import copy
import io
import json
import pytest
from pathlib import Path
from cfb_analytics import poll_refresh

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("include_cfp", [True, False])
def test_live_poll_refresh_retains_last_independently_dated_cfp(tmp_path, monkeypatch, include_cfp):
    existing = json.loads((ROOT / 'data/poll-2026-snapshot.json').read_text())
    directory = tmp_path / 'data'
    directory.mkdir()
    target = directory / 'poll-2026-snapshot.json'
    target.write_text(json.dumps(existing))
    response = [{'season': 2026, 'week': 12, 'polls': [
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
    assert updated['week'] == 12
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
