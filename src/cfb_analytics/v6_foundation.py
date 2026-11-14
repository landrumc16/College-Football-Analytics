"""Validated, descriptive V6 team-season observations; no production-model inputs.

Retrieval proves availability now, not before an old game's kickoff. Historic
biography experience is deliberately not treated as season-specific experience.
"""
from __future__ import annotations

from collections import Counter
from math import isfinite, fsum
from .historical import utc_instant


def finite_mean(values):
    values = [value for value in values if value is not None]
    if not values:
        return None
    if any(type(value) not in (int, float) or not isfinite(value) for value in values):
        raise ValueError("Non-finite source value")
    return fsum(values) / len(values)


def recruiting_summary(rows):
    seen = set()
    for row in rows:
        key = str(row['recruit_id'])
        if not row['recruit_id'] or key in seen:
            raise ValueError('Missing/duplicate recruit identity')
        seen.add(key)
        if row.get('stars') is not None and row['stars'] not in (1, 2, 3, 4, 5):
            raise ValueError('Invalid recruiting stars')
        if row.get('grade') is not None and (not isfinite(row['grade']) or row['grade'] < 0):
            raise ValueError('Invalid recruiting grade')
    rated = [row for row in rows if row.get('stars') is not None]
    graded = [row for row in rows if row.get('grade') is not None]
    return {'players': len(rows), 'star_rated': len(rated), 'grade_rated': len(graded),
            'mean_stars': finite_mean([row['stars'] for row in rated]),
            'mean_publisher_grade': finite_mean([row['grade'] for row in graded]),
            'source_grades_over_100': sum(row['grade'] > 100 for row in graded),
            'grade_scale': 'publisher grade units; not a percentage or CFBD recruiting points',
            'blue_chip_share': sum(row['stars'] >= 4 for row in rated) / len(rated) if rated else None}


def roster_summary(rows, previous_ids, *, current_season=False):
    ids = [str(row['athlete_id']) for row in rows]
    if len(ids) != len(set(ids)) or any(not row['athlete_id'] for row in rows):
        raise ValueError('Missing/duplicate roster identity')
    retained = len(set(ids) & previous_ids) if previous_ids is not None else None
    experiences = [row['experience_years'] for row in rows if current_season and row.get('experience_years') is not None]
    if any(not isfinite(x) or not 0 <= x <= 15 for x in experiences):
        raise ValueError('Invalid roster experience')
    return {'players': len(ids), 'returning_observed_players': retained,
            'retained_share_of_prior_roster': retained / len(previous_ids) if previous_ids else None,
            'returning_share_of_current_roster': retained / len(ids) if retained is not None and ids else None,
            'experience_observations': len(experiences), 'reported_mean_experience': finite_mean(experiences),
            'experience_status': 'current_snapshot_not_independently_corroborated' if current_season else 'excluded_historical_biography_backfill_risk',
            'scope': 'observed roster membership; not snaps, returning production, or proof of playing eligibility'}


def validate_foundation(payload):
    if payload.get('schema_version') != 1 or payload.get('historical_asof_verified') is not False:
        raise ValueError('Foundation must declare its historical availability limitation')
    if utc_instant(payload.get('knowledge_as_of')) is None:
        raise ValueError('Missing timezone-aware knowledge date')
    seen, domains = set(), Counter()
    for row in payload.get('team_seasons', []):
        key = (row['season'], row['team'])
        if key in seen or type(row['season']) is not int or not row['team']:
            raise ValueError('Duplicate/invalid team-season')
        seen.add(key)
        if not row['source_ids'] and any(row[name] is not None for name in ('recruiting', 'roster', 'coaching')):
            raise ValueError('Missing source lineage')
        for domain in ('recruiting', 'roster', 'coaching'):
            if row[domain] is not None:
                domains[domain] += 1
        for name in ('roster', 'recruiting'):
            if row[name] is not None and row[name]['players'] <= 0:
                raise ValueError('Empty observations must remain unavailable')
        roster = row['roster']
        if roster and row['season'] < payload['latest_season'] and roster['reported_mean_experience'] is not None:
            raise ValueError('Historical biography backfill cannot be season experience')
        for name in ('blue_chip_share',):
            value = row['recruiting'].get(name) if row['recruiting'] else None
            if value is not None and (not isfinite(value) or not 0 <= value <= 1):
                raise ValueError('Invalid recruiting proportion')
        if roster:
            for name in ('retained_share_of_prior_roster', 'returning_share_of_current_roster'):
                value = roster[name]
                if value is not None and (not isfinite(value) or not 0 <= value <= 1):
                    raise ValueError('Invalid roster proportion')
    if not seen or any(domains[name] == 0 for name in ('recruiting', 'roster', 'coaching')):
        raise ValueError('All required domains need actual observations')
    return {'team_seasons': len(seen), 'domain_team_seasons': dict(domains)}


def require_historical_pregame_eligibility(payload, cutoff):
    """Fail closed; a class year never turns a retrospective snapshot into evidence."""
    if utc_instant(cutoff) is None:
        raise ValueError('Invalid forecast cutoff')
    if payload.get('historical_asof_verified') is not True:
        raise ValueError('Historical pregame availability is not verified')
    if utc_instant(payload['knowledge_as_of']) >= utc_instant(cutoff):
        raise ValueError('Snapshot is not strictly before forecast cutoff')


def validate_registry(registry):
    """A versioned URL and exact bytes are required, not just a provider name."""
    import re
    from pathlib import PurePath
    if registry.get('schema_version') != 1 or not registry.get('license'):
        raise ValueError('Missing registry or reuse terms')
    commit = registry.get('upstream_commit', '')
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Source reference is not immutable')
    seen = set()
    for source in registry.get('sources', []):
        if source['id'] in seen or not re.fullmatch(r'[0-9a-f]{64}', source['sha256']):
            raise ValueError('Duplicate source or invalid checksum')
        seen.add(source['id'])
        if not source['url'].startswith('https://') or '/' + commit + '/' not in source['url']:
            raise ValueError('Unpinned source URL')
        if PurePath(source['cache_name']).name != source['cache_name']:
            raise ValueError('Cache name must be a file basename')
        if utc_instant(source['retrieved_at']) is None:
            raise ValueError('Missing source retrieval date')
    if not seen:
        raise ValueError('Empty source registry')
    return seen


def load_foundation(root):
    """Hash-check the public derived corpus and its retained identity/provenance inputs."""
    import gzip
    import hashlib
    import json
    from pathlib import Path
    root = Path(root)
    manifest = json.loads((root / 'research/v6/manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Retained research checksum mismatch: ' + name)
    registry = json.loads((root / 'research/v6/sources.json').read_text())
    ids = validate_registry(registry)
    canonical = gzip.decompress((root / 'research/v6/foundation.json.gz').read_bytes())
    if __import__('hashlib').sha256(canonical).hexdigest() != manifest['canonical_foundation_sha256']:
        raise ValueError('Canonical foundation checksum mismatch')
    payload = json.loads(canonical)
    validate_foundation(payload)
    if any(source not in ids for row in payload['team_seasons'] for source in row['source_ids']):
        raise ValueError('Unresolved source lineage')
    return payload
