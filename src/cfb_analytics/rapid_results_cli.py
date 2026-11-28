"""Process an authorized inbox without making provider requests."""
import argparse
import hashlib
from scripts.reconcile_v5_historical_sources import canonical
from .v5_fast_updates import _timestamp
import json
from pathlib import Path
from .rapid_results import transition, save_state, public_snapshot, export_confirmed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('inbox', 'schedule', 'sources', 'state', 'output', 'archive'):
        p.add_argument('--'+name, required=True, type=Path)
    p.add_argument('--cfbd-snapshot', type=Path)
    p.add_argument('--confirmed-games', type=Path)
    a = p.parse_args()
    schedule = json.loads(a.schedule.read_text())
    if isinstance(schedule, dict): schedule = schedule['schedule']
    registry = json.loads(a.sources.read_text())
    sources = registry.get('sources', {}) if registry.get('enabled') is True else {}
    state = json.loads(a.state.read_text()) if a.state.exists() else None
    revision = state['revision'] if state else 0
    inbox = json.loads(a.inbox.read_text()) if a.inbox.exists() else {'batch_id': None, 'observations': []}
    batch_id = inbox.get('batch_id')
    digest = hashlib.sha256(json.dumps(inbox, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    prior_digest = (state or {}).get('batch_digests', {}).get(batch_id)
    if prior_digest and prior_digest != digest:
        raise ValueError('Batch ID reused with different content')
    envelopes = [] if prior_digest == digest else inbox['observations']
    for envelope in envelopes:
        if envelope.get('authoritative'):
            raise ValueError('Rapid inbox cannot attest CFBD verification')
        state = transition(state, envelope['observation'], schedule, sources)
    if a.cfbd_snapshot and state:
        snapshot = json.loads(a.cfbd_snapshot.read_text())
        games = snapshot.get('games', snapshot.get('schedule', [])) if isinstance(snapshot, dict) else snapshot
        source = 'https://api.collegefootballdata.com/games'
        for game in games:
            gid = game.get('game_id', game.get('id'))
            if not game.get('completed') or not any(str(e['game_id']) == str(gid) for e in state['events']): continue
            at = snapshot.get('retrieved_at') if isinstance(snapshot, dict) else None
            if not at: raise ValueError('CFBD snapshot needs retrieved_at receipt')
            prior = next(e for e in state['events'] if str(e['game_id']) == str(gid))
            if _timestamp(at) < _timestamp(prior['observed_at']): continue
            row = {'kind':'game_final', 'status':'final', 'game_id':gid,
                   'home':canonical(game.get('home', game.get('homeTeam'))), 'away':canonical(game.get('away', game.get('awayTeam'))),
                   'home_score':game.get('home_score', game.get('homePoints')), 'away_score':game.get('away_score', game.get('awayPoints')),
                   'source':source, 'published_at':at, 'observed_at':at}
            state = transition(state, row, schedule, sources, authoritative=True)
    if state is None: return
    if batch_id: state.setdefault('batch_digests', {})[batch_id] = digest
    batches = state.setdefault('processed_batch_ids', [])
    if inbox.get('batch_id') and inbox['batch_id'] not in batches: batches.append(inbox['batch_id'])
    save_state(a.state, state, expected_revision=revision)
    export_confirmed(state, a.archive)
    if a.confirmed_games:
        confirmed = [e for e in state['events'] if e['model_ingestion_allowed']]
        a.confirmed_games.write_text(json.dumps(confirmed, indent=2)+'\n')
    # Reuse the atomic JSON publisher's replace convention. The state is durable
    # first; a failed export can safely be retried from the same inbox.
    a.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.output.with_suffix('.tmp')
    tmp.write_text(json.dumps(public_snapshot(state, schedule), indent=2)+'\n')
    tmp.replace(a.output)

if __name__ == '__main__': main()
