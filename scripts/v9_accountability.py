"""Offline V9 accountability: retain issued values, never reconstruct past predictions."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

from cfb_analytics.forecast_ledger import aware_utc, ALIASES
from cfb_analytics.v5_forecast_evaluation import evaluate_archived_forecasts

MODELS = ('official', 'standard', 'momentum')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(name):
    return ALIASES.get(name, name)


def valid_probability(value):
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1


def retain(archive, report, dual, snapshot, *, now, receipts):
    """Exclusive first observation per game/model. Existing bytes are never rewritten."""
    clock = aware_utc(now)
    if clock is None:
        raise ValueError('Retention requires a timezone-aware clock')
    archive.mkdir(parents=True, exist_ok=True)
    games = {str(g['game_id']): g for g in snapshot['games']}
    candidates = [('official', p, report.get('generated_at'), report.get('retrieved_at'), report.get('model_metadata', {}).get('model_id')) for p in report['predictions']]
    for p in dual['games']:
        for model in ('standard', 'momentum'):
            if p.get(model):
                candidates.append((model, {**p, **p[model]}, dual.get('generated_at'), dual.get('data_retrieved_at'), 'released_dual_' + model))
    retained = 0
    for model, p, generated, retrieved, version in candidates:
        game = games.get(str(p.get('game_id')))
        if not game or game.get('completed') or not version or not valid_probability(p.get('home_win_probability')):
            continue
        kickoff, created, source = map(aware_utc, (game.get('start_date'), generated, retrieved))
        if not all((kickoff, created, source)) or not source <= created <= clock < kickoff:
            continue
        home, away = canonical(game.get('home')), canonical(game.get('away'))
        if (p.get('home'), p.get('away')) != (home, away):
            continue
        row = {'schema_version': 1, 'season': report['season'], 'game_id': str(game['game_id']), 'model_id': model,
               'model_version': version, 'home': home, 'away': away,
               'home_win_probability': p['home_win_probability'], 'home_margin': p.get('home_margin'),
               'prediction_time': generated, 'source_retrieved_at': retrieved, 'retained_at': now,
               'kickoff_time': game['start_date'], 'source': 'first_retained_before_kickoff', 'source_receipts': receipts}
        target = archive / f"{report['season']}-{game['game_id']}-{model}.json"
        with tempfile.NamedTemporaryFile(mode='w', dir=archive, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, target)
            retained += 1
        except FileExistsError:
            existing = json.loads(target.read_text())
            if (existing.get('game_id'), existing.get('model_id')) != (row['game_id'], model):
                raise ValueError('Archive identity conflict')
        finally:
            temporary.unlink()
    return retained


def evaluate(history, retained, snapshot, roster):
    """Reuse the existing strict scorer; independently label legacy vs new retention evidence."""
    games = {str(g['game_id']): g for g in snapshot['games']}
    candidates = []
    exclusions = Counter()
    for key, entry in history.items():
        if entry.get('source') != 'generated_before_kickoff':
            exclusions['legacy_without_complete_pregame_evidence'] += 1
            continue
        candidates.append({**entry, 'game_id': str(key), 'model_id': 'official', 'model_version': entry.get('model_id'),
                           'prediction_time': entry.get('forecast_recorded_at'), 'kickoff_time': entry.get('scheduled_kickoff_at'),
                           'evidence_kind': 'existing_generation_ledger'})
    for row in retained:
        if row.get('schema_version') != 1 or row.get('source') != 'first_retained_before_kickoff' or not isinstance(row.get('source_receipts'), dict):
            exclusions['invalid_retained_archive_shape'] += 1
            continue
        candidates.append({**row, 'evidence_kind': 'v9_first_retention'})
    selected = {}
    for row in candidates:
        key = (str(row.get('game_id')), row.get('model_id'))
        game = games.get(key[0])
        if key[1] not in MODELS or not game:
            exclusions['missing_game_or_model'] += 1; continue
        if canonical(game['home']) not in roster or canonical(game['away']) not in roster:
            exclusions['non_fbs_matchup'] += 1; continue
        if not game.get('completed'):
            exclusions['unsettled_forecast'] += 1; continue
        hs, aws = game.get('home_score'), game.get('away_score')
        if any(isinstance(s, bool) or not isinstance(s, (int, float)) or not math.isfinite(s) for s in (hs, aws)) or hs == aws:
            exclusions['invalid_or_tied_final_score'] += 1; continue
        if (row.get('home'), row.get('away')) != (canonical(game['home']), canonical(game['away'])):
            exclusions['identity_mismatch'] += 1; continue
        created, source, kickoff, actual_kickoff = map(aware_utc, (row.get('prediction_time'), row.get('source_retrieved_at'), row.get('kickoff_time'), game.get('start_date')))
        retained_at = aware_utc(row.get('retained_at')) if row.get('evidence_kind') == 'v9_first_retention' else created
        outcome_asof = aware_utc(snapshot.get('retrieved_at'))
        if (not all((created, source, kickoff, actual_kickoff, retained_at, outcome_asof)) or not source <= created <= retained_at < kickoff <= outcome_asof or kickoff != actual_kickoff or not row.get('model_version') or not valid_probability(row.get('home_win_probability'))):
            exclusions['invalid_timing_version_or_probability'] += 1; continue
        candidate = {**row, 'game_id': key[0], 'home_won': hs > aws}
        # Prefer the earliest legitimate issued value when a game also occurs in the older ledger.
        if key not in selected or created < aware_utc(selected[key]['prediction_time']):
            selected[key] = candidate
    eligible = sum(1 for g in games.values() if g.get('completed') and canonical(g['home']) in roster and canonical(g['away']) in roster and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in (g.get('home_score'),g.get('away_score'))) and g['home_score'] != g['away_score'])
    rows = list(selected.values())
    metrics = evaluate_archived_forecasts(rows)
    common_ids = {r['game_id'] for r in rows if all((r['game_id'], m) in selected for m in MODELS)}
    common = evaluate_archived_forecasts([r for r in rows if r['game_id'] in common_ids])
    return {'schema_version': 1, 'status': 'retained_pregame_evidence_not_independent_publication_verification',
            'outcome_as_of': snapshot.get('retrieved_at'), 'eligible_completed_games': eligible, 'models': {m: metrics['models'].get(m) for m in MODELS},
            'common_games': len(common_ids), 'common_models': {m: common['models'].get(m) for m in MODELS},
            'evidence_counts': dict(Counter(r['evidence_kind'] for r in rows)), 'exclusions': dict(exclusions),
            'model_versions': {m: sorted({r['model_version'] for r in rows if r['model_id'] == m}) for m in MODELS},
            'limitations': ['Existing ledger timestamps establish generation evidence, not independent public release time.',
                           'No Standard or Momentum replay enters the retained-pregame cohort.',
                           'Only all-three common completed FBS games support direct model comparisons.',
                           'Small samples and individual calibration bins do not establish a reliable future edge.',
                           'Matched games do not guarantee identical information cutoffs; inspect timestamp and version receipts.',
                           'Historical source correction cannot rewrite an issued forecast; outcome corrections may change scores.'],
            'scored_rows': rows}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--archive', type=Path, default=Path('docs/evidence/v9/pregame'))
    parser.add_argument('--retain', action='store_true')
    args = parser.parse_args()
    paths = {'report': Path('data/season-2026-report.json'), 'dual': Path('web/public/dual-projections.json'),
             'snapshot': Path('data/cfbd-2026-games.json'), 'legacy_ledger': Path('data/pregame-2026-history.json')}
    raw = {k: p.read_bytes() for k, p in paths.items()}
    data = {k: json.loads(v) for k, v in raw.items()}
    receipts = {k: {'path': str(paths[k]), 'sha256': digest(v)} for k, v in raw.items()}
    if args.retain:
        retain(args.archive, data['report'], data['dual'], data['snapshot'], now=datetime.now(timezone.utc).isoformat(), receipts=receipts)
    retained = [json.loads(p.read_text()) for p in sorted(args.archive.glob('*.json'))] if args.archive.exists() else []
    result = evaluate(data['legacy_ledger'], retained, data['snapshot'], {r['team'] for r in data['report']['rankings']})
    result.update(source_receipts=receipts, retained_forecasts=len(retained))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, allow_nan=False) + '\n')
    print(f"Retained {len(retained)} forecasts; scored " + ', '.join(f"{k}={v['games'] if v else 0}" for k,v in result['models'].items()) + f"; common={result['common_games']}")


if __name__ == '__main__':
    main()
