"""Provider-neutral rapid finals, with durable reconciliation and no network access.

Adapters must supply canonical game IDs from the retained schedule. Source permission
is enforced at the inbox boundary; an URL alone never authorizes acquisition.
"""
import copy
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from .v5_fast_updates_cli import publish
from .v5_fast_updates import _timestamp


def _bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def transition(state, observation, schedule, authorized_sources, *, authoritative=False):
    """Apply one observation, preserving history and allowing CFBD corrections.

    Provisional records are presentation-only; prediction models continue to consume
    confirmed canonical season data. CFBD verification does not pretend that CFBD
    and ESPN are independent sources.
    """
    row = copy.deepcopy(observation)
    if row.get('source') not in authorized_sources:
        raise ValueError('Source is not authorized')
    if authoritative and (authorized_sources[row['source']] != 'cfbd' or row['source'] != 'https://api.collegefootballdata.com/games'):
        raise ValueError('Authoritative reconciliation requires CFBD')
    if row.get('kind') != 'game_final':
        raise ValueError('Only game finals supported')
    observed = _timestamp(row.get('observed_at'))
    if _timestamp(row.get('published_at')) > observed:
        raise ValueError('Publication timestamp exceeds observation')
    expected = next((g for g in schedule if str(g['game_id']) == str(row.get('game_id'))), None)
    if expected is None or any(expected[k] != row.get(k) for k in ('home', 'away')):
        raise ValueError('Game identity does not match retained schedule')
    kickoff = expected.get('start_date')
    if kickoff and observed < _timestamp(kickoff):
        raise ValueError('Final observed before kickoff')
    if expected.get('completed') and not authoritative and any(expected.get(k) != row.get(k) for k in ('home_score', 'away_score')):
        raise ValueError('Secondary result conflicts with retained confirmed final')
    if row.get('home_score') == row.get('away_score'):
        raise ValueError('Final game cannot be tied')
    stats = row.get('basic_stats', {})
    if not isinstance(stats, dict) or any(side not in ('home', 'away') for side in stats):
        raise ValueError('Invalid basic statistics')
    for values in stats.values():
        if not isinstance(values, dict) or any(k not in ('total_yards', 'passing_yards', 'rushing_yards', 'turnovers', 'first_downs') or type(v) is not int or v < 0 for k, v in values.items()):
            raise ValueError('Invalid basic statistics')
    # Reuse the V5 validation and conservative upstream confirmation policy.
    checked = publish([row])
    out = copy.deepcopy(state or {'schema_version': 1, 'revision': 0, 'events': [], 'history': []})
    prior = next((e for e in out['events'] if str(e['game_id']) == str(row['game_id'])), None)
    identity = hashlib.sha256(_bytes({'row': row, 'authoritative': authoritative})).hexdigest()
    if any(h['id'] == identity for h in out['history']):
        return out
    if prior and _timestamp(row['observed_at']) < _timestamp(prior['observed_at']):
        raise ValueError('Refusing stale observation')
    changed = prior and (prior['home_score'], prior['away_score']) != (row['home_score'], row['away_score'])
    if prior and prior['model_ingestion_allowed'] and not authoritative:
        # A secondary feed cannot displace a verified final.
        status = 'disputed' if changed else prior['status']
        event = copy.deepcopy(prior)
        event['status'] = status
    else:
        status = ('corrected' if changed else 'confirmed') if authoritative else checked['status']
        event = {k: row[k] for k in ('game_id', 'home', 'away', 'home_score', 'away_score', 'source', 'observed_at')}
        retained_stats = stats or (prior.get('basic_stats', {}) if prior and authoritative else {})
        event.update(status=status, basic_stats=retained_stats, statistics_verified=bool(stats) and authoritative, statistics_source=row['source'] if stats else prior.get('statistics_source', prior.get('source')) if prior else row['source'], verified_at=row['observed_at'] if authoritative else None,
                     statistics_pending=not all(set(retained_stats.get(side, {})) >= {'total_yards', 'passing_yards', 'rushing_yards', 'turnovers', 'first_downs'} for side in ('home', 'away')), model_ingestion_allowed=authoritative)
    out['events'] = [e for e in out['events'] if str(e['game_id']) != str(row['game_id'])] + [event]
    out['revision'] += 1
    out['history'].append({'id': identity, 'revision': out['revision'], 'observation': row, 'authoritative': authoritative, 'result': event})
    out['generated_at'] = row['observed_at']
    return out


def public_snapshot(state, schedule):
    """Derive score-based records; never invent detailed statistics or ratings."""
    records = {}
    games = {str(g['game_id']): g for g in schedule if g.get('completed')}
    games.update({str(e['game_id']): e for e in state['events']})
    for game in games.values():
        for side, other in (('home', 'away'), ('away', 'home')):
            r = records.setdefault(game[side], {'wins': 0, 'losses': 0, 'provisional_games': 0})
            r['wins' if game[side+'_score'] > game[other+'_score'] else 'losses'] += 1
            r['provisional_games'] += game.get('status') == 'provisional'
    return {k: v for k, v in state.items() if k != 'history'} | {'records': records}


def save_state(path, state, *, expected_revision):
    """Serialize writers; reject stale writes. State is the single atomic commit.

    History is append-only inside this transaction, so a crash cannot publish a
    result without its evidence. Immutable archive exports are reproducible.
    """
    import fcntl
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(path.suffix+'.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        old = json.loads(path.read_text()) if path.exists() else {'revision': 0, 'history': []}
        if old['revision'] != expected_revision:
            raise ValueError('Concurrent update; reload and retry')
        if state['history'][:len(old['history'])] != old['history']:
            raise ValueError('Refusing archive history rewrite')
        fd, tmp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(_bytes(state)); f.flush(); os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)


def export_confirmed(state, directory):
    """Content-addressed evidence; existing bytes are never replaced."""
    root = Path(directory); root.mkdir(parents=True, exist_ok=True)
    for item in state['history']:
        if not item['authoritative']:
            continue
        path = root / (item['id']+'.json')
        data = _bytes(item)
        if path.exists():
            if path.read_bytes() != data: raise ValueError('Immutable archive mismatch')
        else:
            fd, temporary = tempfile.mkstemp(dir=root)
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(data); f.flush(); os.fsync(f.fileno())
                try:
                    os.link(temporary, path)  # expose only complete bytes; never replace an archive
                except FileExistsError:
                    if path.read_bytes() != data:
                        raise ValueError('Immutable archive mismatch')
            finally:
                os.unlink(temporary)
