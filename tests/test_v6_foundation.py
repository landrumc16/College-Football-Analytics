"""Source-quality and temporal safeguards; synthetic fixtures never enter publications."""
from copy import deepcopy
from pathlib import Path
import json
import pytest
from cfb_analytics.v6_foundation import (
    finite_mean, recruiting_summary, roster_summary, require_historical_pregame_eligibility,
    validate_foundation, validate_registry, load_foundation,
)

ROOT = Path(__file__).resolve().parents[1]


def test_retained_real_corpus_and_all_domain_coverage():
    payload = load_foundation(ROOT)
    assert len(payload['team_seasons']) == 1452
    counts = validate_foundation(payload)['domain_team_seasons']
    assert counts == {'recruiting': 1449, 'roster': 1449, 'coaching': 1450}
    assert payload['coverage'][-1]['all_domains'] == 138
    historical = [r for r in payload['team_seasons'] if r['season'] < 2026 and r['roster']]
    assert all(r['roster']['reported_mean_experience'] is None for r in historical)
    assert all(r['historical_pregame_eligible'] is False for r in payload['team_seasons'])


def test_missing_ratings_are_not_zero_and_grade_is_not_a_percentage():
    rows = [{'recruit_id':'fixture-a','stars':None,'grade':None},
            {'recruit_id':'fixture-b','stars':5,'grade':100.3}]
    result = recruiting_summary(rows)
    assert result['mean_stars'] == 5 and result['star_rated'] == 1
    assert result['mean_publisher_grade'] == 100.3 and result['source_grades_over_100'] == 1
    assert result['blue_chip_share'] == 1
    assert finite_mean([None]) is None
    assert finite_mean([1e16, 1, -1e16]) == 1 / 3
    with pytest.raises(ValueError):recruiting_summary(rows + [rows[0]])
    with pytest.raises(ValueError):finite_mean([float('nan')])


def test_roster_overlap_is_not_production_or_historical_experience():
    rows = [{'athlete_id':'fixture-a','experience_years':4}, {'athlete_id':'fixture-c','experience_years':1}]
    result = roster_summary(rows, {'fixture-a','fixture-b'})
    assert result['returning_observed_players'] == 1
    assert result['retained_share_of_prior_roster'] == .5
    assert result['reported_mean_experience'] is None
    assert roster_summary(rows, None)['returning_observed_players'] is None
    with pytest.raises(ValueError):roster_summary(rows + [rows[0]], set())


def test_historical_retrieval_does_not_become_pregame_evidence():
    payload = load_foundation(ROOT)
    for cutoff in ['2019-09-01T00:00:00Z','2026-11-20T00:00:00Z']:
        with pytest.raises(ValueError,match='not verified'):
            require_historical_pregame_eligibility(payload,cutoff)
    payload['historical_asof_verified'] = True
    with pytest.raises(ValueError,match='strictly before'):
        require_historical_pregame_eligibility(payload,payload['knowledge_as_of'])


@pytest.mark.parametrize('field,value', [('sha256','bad'),('retrieved_at','2019-01-01'),('url','https://example.com/latest'),('cache_name','../escape')])
def test_registry_rejects_unverifiable_inputs(field,value):
    registry = json.loads((ROOT/'research/v6/sources.json').read_text())
    registry['sources'][0][field] = value
    with pytest.raises(ValueError):validate_registry(registry)


def test_duplicate_and_backfilled_records_fail_validation():
    payload = load_foundation(ROOT)
    payload['team_seasons'].append(deepcopy(payload['team_seasons'][0]))
    with pytest.raises(ValueError,match='Duplicate'):validate_foundation(payload)
    payload = load_foundation(ROOT)
    payload['team_seasons'][0]['roster']['reported_mean_experience'] = 4
    with pytest.raises(ValueError,match='backfill'):validate_foundation(payload)


def test_raw_checksum_change_prevents_replay(tmp_path):
    from scripts.build_v6_foundation import acquire
    registry = json.loads((ROOT/'research/v6/sources.json').read_text())
    registry['sources'] = registry['sources'][:1]
    with pytest.raises(ValueError,match='Missing retained'):acquire(registry,tmp_path,offline=True)
    (tmp_path/registry['sources'][0]['cache_name']).write_bytes(b'not original bytes')
    with pytest.raises(ValueError,match='checksum mismatch'):acquire(registry,tmp_path,offline=True)
