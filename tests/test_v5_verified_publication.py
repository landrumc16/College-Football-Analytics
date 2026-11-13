"""Release evidence: replay retained real sources, not illustrative grades."""
import copy
import hashlib
import json
import pytest
from scripts import reconcile_v5_historical_sources as historical
from scripts import verify_v5_pregame_archive as forecasts


def test_real_historical_publication_replays_offline(monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request, 'urlopen', lambda *a, **k: pytest.fail('Offline replay attempted network access'))
    records, polls, cards, comparison = historical.reconcile()
    assert records == historical.read(historical.ARCHIVE / 'accepted-team-seasons.json')
    assert polls == historical.read(historical.ARCHIVE / 'accepted-poll-history.json.gz')
    assert cards == historical.read(historical.ROOT / 'web/public/v5-program-report-cards.json')
    assert comparison == historical.read(historical.ARCHIVE / 'comparison.json')
    assert comparison['accepted_team_seasons'] == 1308
    assert comparison['poll_snapshots_compared'] == 40
    assert comparison['ranked_placements_compared'] == 1000
    assert {r['season'] for r in comparison['season_exceptions']} == {2020}
    assert {r['game_id'] for r in comparison['score_exceptions']} == {'401014983', '401021686', '401309645'}
    assert sum(r['matching_fbs_game_scores'] for r in comparison['game_coverage']) == 7557
    assert cards['eligible_fbs_count'] == 138
    assert cards['coverage']['hype']['verified'] == 127
    assert cards['coverage']['trajectory']['verified'] == 127
    assert cards['coverage']['strength']['verified'] == 138
    assert sum(p['overall_score'] is not None for p in cards['programs']) == 127
    assert next(p for p in cards['programs'] if p['team'] == 'North Dakota State')['overall_score'] is None


def test_disputed_poll_cannot_be_published(monkeypatch):
    read = historical.read
    def altered(path):
        value = read(path)
        if path.name == 'independent-polls.json':
            value = copy.deepcopy(value)
            value['snapshots'][0]['rows'][0]['rank'] = 25
        return value
    monkeypatch.setattr(historical, 'read', altered)
    with pytest.raises(ValueError, match='independent'):
        historical.reconcile()


def test_immutable_pregame_publication_and_independent_outcomes_replay():
    rows, matches, report = forecasts.verify()
    assert rows == historical.read(historical.ARCHIVE / 'verified-pregame-rows.json')
    assert matches == historical.read(historical.ARCHIVE / 'pregame-outcome-matches.json')
    assert report == historical.read(historical.ROOT / 'web/public/v5-forecast-evaluation.json')
    metrics = report['models']['workbook_2026_baseline']
    assert metrics['games'] == 57
    assert metrics['accuracy'] == pytest.approx(35 / 57)
    assert metrics['brier'] == pytest.approx(.22267659330851503)
    assert metrics['logloss'] == pytest.approx(.6385431864221272)
    assert sum(x['games'] for x in metrics['confidence_segments'].values()) == 57
    assert report['models']['neutral_50_50']['games'] == 57
    assert len(report['paired_baseline_comparisons']) == 1


def test_changed_published_forecast_is_rejected(monkeypatch):
    read = forecasts.read
    def altered(path):
        value = read(path)
        if path.name == 'pregame-2026-history.json':
            value = copy.deepcopy(value)
            value['401856738']['home_win_probability'] = .01
        return value
    monkeypatch.setattr(forecasts, 'read', altered)
    with pytest.raises(ValueError, match='modified'):
        forecasts.verify()


def test_retained_input_checksums():
    manifest = historical.read(historical.ARCHIVE / 'manifest.json')
    for entry in manifest['inputs']:
        raw = (historical.ARCHIVE / entry['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == entry['sha256'], entry['path']
