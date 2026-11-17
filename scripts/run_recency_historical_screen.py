"""Historical 2022-2025 neutral-prior research screen, NOT incumbent promotion evidence.

Uses independently corroborated completed FBS games; all teams receive a neutral
zero prior. Neither model receives future results. This reference baseline is NOT
the season-specific historical incumbent, whose true priors are unavailable.
"""
import argparse
import gzip
import json
from pathlib import Path
from cfb_analytics.ratings import Team
from cfb_analytics.recency_replay_research import paired_replay, paired_metrics
from cfb_analytics.v4_evaluation import evaluate_pairs, clustered_brier_interval

ROOT = Path(__file__).resolve().parents[1]
DISPUTED = {'401014983', '401021686', '401309645'}
SEASONS = (2022, 2023, 2024, 2025)

def run():
    archive = ROOT / 'research/archive/verified/espn-games.json.gz'
    with gzip.open(archive, 'rt', encoding='utf-8') as fh:
        seasons = json.load(fh)
    all_pairs = []
    season_summaries = {}
    for season in SEASONS:
        records = []
        for game in seasons[str(season)]:
            if game.get('fbs_game') is not True or str(game['game_id']) in DISPUTED:
                continue
            records.append({
                'game_id': str(game['game_id']), 'start_date': game.get('kickoff') or game.get('start_date'),
                'home': game['home'], 'away': game['away'],
                'home_score': game['home_score'], 'away_score': game['away_score'],
                'completed': True, 'neutral_site': game.get('neutral_site', False),
                'week': int(game['week']),
            })
        names = sorted({g[k] for g in records for k in ('home', 'away')})
        teams = [Team(name, 'Neutral research pool', 0.0) for name in names]
        replay = paired_replay(teams, records)
        if len(replay) != len(records):
            raise ValueError(f'{season}: dropped games during replay')
        pairs = [{
            'season': season, 'week': r['week'], 'game_id': r['game_id'],
            'outcome': r['home_won'], 'prediction_kind': 'retrospective',
            'incumbent_probability': r['incumbent_probability'],
            'challenger_probability': r['challenger_probability'],
        } for r in replay]
        all_pairs.extend(pairs)
        season_summaries[str(season)] = {
            'games': len(replay), 'neutral_prior_reference': paired_metrics(replay),
        }
    evaluation = evaluate_pairs(all_pairs)
    interval = clustered_brier_interval(all_pairs, draws=2000, seed=2026)
    return {
        'status': 'research_only_not_promotion_eligible',
        'source': str(archive.relative_to(ROOT)),
        'seasons': season_summaries,
        'paired_games': len(all_pairs),
        'evaluation': evaluation,
        'clustered_brier_interval': interval,
        'limitations': [
            'Both arms use neutral zero priors and one synthetic conference pool; this is NOT a reconstruction of the historical incumbent.',
            'Retrospective kickoff+4h availability is an assumption, not independently verified final-score publication timing.',
            'No archived 2022-2025 pregame forecasts exist. This is a retrospective model comparison, not live forecast accuracy.',
            'No hyperparameter tuning or model promotion is authorized by this research screen.',
        ],
        'production_changed': False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n')
    print(json.dumps({'games': result['paired_games'],
                      'pooled': result['evaluation']['retrospective'],
                      'ci': result['clustered_brier_interval'],
                      'promotion_eligible': False}, indent=2))

if __name__ == '__main__':
    main()
