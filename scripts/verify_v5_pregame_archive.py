"""Replay the frozen, published forecast cohort against retained independent finals."""
import csv
import gzip
import hashlib
from collections import defaultdict
from datetime import datetime

from scripts.reconcile_v5_historical_sources import ARCHIVE, ROOT, ncaa_inputs, read, write
from cfb_analytics.v5_forecast_evaluation import evaluate_archived_forecasts, _timestamp


def verify():
    receipt = read(ARCHIVE / 'pregame-publication-receipt.json')
    raw = gzip.decompress((ARCHIVE / 'published-pregame-2026-11-05.json.gz').read_bytes())
    if hashlib.sha256(raw).hexdigest() != receipt['ledger_sha256']:
        raise ValueError('Published pregame ledger hash mismatch')
    if receipt['conclusion'] != 'success' or receipt['commit'] != receipt['workflow_head_sha']:
        raise ValueError('Missing immutable publication evidence')
    import json
    frozen = json.loads(raw)
    current = read(ROOT / 'data/pregame-2026-history.json')
    report = read(ARCHIVE / 'pregame-evaluation-outcomes.json')
    rosters, _, resolve = ncaa_inputs()
    eligible = set(rosters[2026].values())
    # Match by season-specific identities and date; NCAA's optional ESPN ID
    # crosswalk is missing or different for five of these fixtures.
    source = ARCHIVE / 'ncaa/ncaa_mfb_schedule_2026.csv.gz'
    index = defaultdict(dict)
    for r in csv.DictReader(gzip.decompress(source.read_bytes()).decode().splitlines()):
        home = rosters[2026].get(r['team_id'])
        away = rosters[2026].get(r['opponent_id'])
        if not home or not away or not r['team_score'].isdigit() or not r['opponent_score'].isdigit():
            continue
        day = datetime.strptime(r['date'], '%m/%d/%Y').date()
        pair = tuple(sorted((home, away)))
        scores = tuple(sorted(((home, int(r['team_score'])), (away, int(r['opponent_score'])))))
        key = (day, r['contest_id'])
        if key in index[pair] and index[pair][key] != scores:
            raise ValueError('Conflicting NCAA final scores')
        index[pair][key] = scores
    rows, matches = [], []
    for g in report['schedule']:
        key = str(g['game_id'])
        f = frozen.get(key)
        if not g['completed'] or not f or f.get('source') != 'generated_before_kickoff':
            continue
        if g['home'] not in eligible or g['away'] not in eligible:
            continue
        if f != current.get(key):
            raise ValueError('Published forecast was modified')
        if (f['home'], f['away']) != (g['home'], g['away']):
            raise ValueError('Forecast/result identity mismatch')
        kickoff = _timestamp(f['scheduled_kickoff_at'])
        if _timestamp(receipt['server_created_at']) >= kickoff:
            raise ValueError('GitHub publication was not pre-kickoff')
        pair = tuple(sorted((g['home'], g['away'])))
        candidates = [(day, contest, scores) for (day, contest), scores in index[pair].items() if abs((day-kickoff.date()).days) <= 1]
        expected = tuple(sorted(((g['home'], g['home_score']), (g['away'], g['away_score']))))
        if len(candidates) != 1 or candidates[0][2] != expected:
            raise ValueError('Missing or conflicting independent final for ' + key)
        rows.append({'game_id': key, 'model_id': f['model_id'],
            'prediction_time': f['forecast_recorded_at'], 'source_retrieved_at': f['source_retrieved_at'],
            'kickoff_time': f['scheduled_kickoff_at'], 'home_win_probability': f['home_win_probability'],
            'home_won': g['home_score'] > g['away_score']})
        matches.append({'game_id': key, 'ncaa_contest_id': candidates[0][1], 'scores': dict(expected),
                        'match': 'canonical team pair + scheduled date + identical final scores'})
    if not rows:
        raise ValueError('No independently verified settled pregame forecasts')
    baseline = [{**r, 'model_id': 'neutral_50_50', 'home_win_probability': .5} for r in rows]
    result = evaluate_archived_forecasts(rows + baseline)
    result.update(status='independently_verified_published_pregame_subset',
        evaluation_scope='2026 Weeks 10–11 FBS-versus-FBS archived subset',
        outcome_as_of=report['retrieved_at'], forecast_publication=receipt,
        eligible_completed_games=report['prediction_accuracy']['eligible_completed_games'],
        forecast_coverage=len(rows)/report['prediction_accuracy']['eligible_completed_games'],
        independent_final_source='https://github.com/sportsdataverse/sportsdataverse-data/releases/download/ncaa_mfb_schedule/ncaa_mfb_schedule_2026.csv.gz',
        limitations=[f'{len(rows)} verified forecasts from two partial weeks; not full-season accuracy or a prediction of future accuracy',
                     'Only frozen, settled FBS-versus-FBS games are scored; legacy records without pregame provenance are excluded',
                     'The 50/50 baseline is a paired neutral reference, not a competing forecast model'])
    return rows, matches, result


def main():
    rows, matches, report = verify()
    write(ARCHIVE / 'verified-pregame-rows.json', rows)
    write(ARCHIVE / 'pregame-outcome-matches.json', matches)
    write(ROOT / 'web/public/v5-forecast-evaluation.json', report)
    print(report['models']['workbook_2026_baseline'])


if __name__ == '__main__':
    main()
