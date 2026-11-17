"""Retrospective season/momentum blend screen; NEVER production promotion evidence.

Uses the verified FBS results archive, neutral priors and a synthetic conference.
No season-specific historical incumbent priors or archived pregame forecasts exist.
Candidate weights are descriptive research, not tuned production parameters.

Each target game is forecast only from games whose kickoff + 4 hours precedes the target kickoff.
Targets sharing the same eligible history share one as-of rating solve (identical results, far faster).
"""
import argparse
import gzip
import json
from datetime import timedelta
from pathlib import Path
from cfb_analytics.ratings import Team, Game, calculate_ratings
from cfb_analytics.predictions import predict
from cfb_analytics.model import ModelSettings
from cfb_analytics.v4_evaluation import clustered_brier_interval
from scripts.recency_replay_research import _utc, paired_metrics
from scripts.strength_blend_research import calculate_strength_components

ROOT = Path(__file__).resolve().parents[1]
SEASONS = (2022, 2023, 2024, 2025)
DISPUTED = {'401014983', '401021686', '401309645'}
WEIGHTS = (0.0, 0.2, 0.3, 0.35, 0.4, 0.5)
WINDOWS = (3, 4)
# V6 promotion gates (docs/V6-MODEL-EVALUATION.md): >=5% pooled Brier improvement, gains in >=3 of 4 seasons,
# <=2% pooled log-loss regression, and a favourable 95% clustered interval.
GATES = {'min_brier_improvement': 0.05, 'min_improving_seasons': 3, 'max_log_loss_regression': 0.02}


def cluster_week(record):
    return int(record['week']) + (100 if record.get('season_type') == 'postseason' else 0)


def run():
    with gzip.open(ROOT / 'research/archive/verified/espn-games.json.gz', 'rt', encoding='utf-8') as fh:
        archive = json.load(fh)
    settings = ModelSettings()
    all_rows = {(window, weight): [] for window in WINDOWS for weight in WEIGHTS}
    season_counts = {}
    for season in SEASONS:
        records = [g for g in archive[str(season)] if g.get('fbs_game') is True and str(g['game_id']) not in DISPUTED]
        records.sort(key=lambda g: (_utc(g.get('kickoff') or g.get('start_date')), str(g['game_id'])))
        names = sorted({g[k] for g in records for k in ('home', 'away')})
        teams = [Team(n, 'Neutral research pool', 0.0) for n in names]
        parsed = [(_utc(g.get('kickoff') or g.get('start_date')), g) for g in records]
        season_counts[str(season)] = len(parsed)
        cache = {}
        for kickoff, target in parsed:
            eligible = [g for dt, g in parsed if dt + timedelta(hours=4) < kickoff]
            key = len(eligible)            # parsed is chronological, so the eligible set is a prefix
            if key not in cache:
                games = [Game(g['home'], g['away'], g['home_score'], g['away_score'], int(g['week'])) for g in eligible]
                base = calculate_ratings(teams, games, settings)
                cache[key] = (base, {w: calculate_strength_components(teams, games, window=w, momentum_weight=1.0,
                                                                      settings=settings, season_ratings=base)
                                     for w in WINDOWS})
            base, by_window = cache[key]
            args = dict(neutral=bool(target.get('neutral_site', False)),
                        home_field_advantage=settings.home_field_advantage, model_scale=settings.win_probability_scale)
            incumbent = predict(target['home'], target['away'], base[target['home']].adaptive_rating,
                                base[target['away']].adaptive_rating, **args)
            for window in WINDOWS:
                components = by_window[window]
                for weight in WEIGHTS:
                    def rating(name):
                        c = components[name]
                        m = c.recent_momentum if c.recent_momentum is not None else c.season_strength
                        return (1 - weight) * c.season_strength + weight * m
                    forecast = predict(target['home'], target['away'], rating(target['home']), rating(target['away']), **args)
                    all_rows[(window, weight)].append({
                        'season': season, 'week': cluster_week(target), 'game_id': str(target['game_id']),
                        'home_won': int(target['home_score'] > target['away_score']),
                        'incumbent_probability': incumbent.model_home_probability,
                        'challenger_probability': forecast.model_home_probability,
                        'incumbent_margin': incumbent.home_margin, 'challenger_margin': forecast.home_margin,
                        'actual_margin': target['home_score'] - target['away_score'],
                    })
    summary = []
    for (window, weight), rows in all_rows.items():
        metrics = paired_metrics(rows)
        by_season = {str(s): paired_metrics([r for r in rows if r['season'] == s]) for s in SEASONS}
        inc, ch = metrics['incumbent'], metrics['challenger']
        brier_gain = (inc['brier'] - ch['brier']) / inc['brier']
        ll_regression = (ch['log_loss'] - inc['log_loss']) / inc['log_loss']
        improving = sum(by_season[s]['challenger']['brier'] < by_season[s]['incumbent']['brier'] for s in by_season)
        entry = {'window': window, 'momentum_weight': weight, 'paired_games': len(rows), 'metrics': metrics,
                 'by_season': by_season, 'relative_brier_improvement': round(brier_gain, 5),
                 'relative_log_loss_regression': round(ll_regression, 5), 'seasons_improved': improving}
        if weight > 0:
            interval = clustered_brier_interval([{'season': r['season'], 'week': r['week'], 'game_id': r['game_id'],
                                                  'outcome': r['home_won'], 'prediction_kind': 'retrospective',
                                                  'incumbent_probability': r['incumbent_probability'],
                                                  'challenger_probability': r['challenger_probability']} for r in rows],
                                                draws=2000, seed=2026)
            entry['clustered_brier_interval'] = interval
            upper = interval['ci95_upper']
            entry['gates'] = {
                'brier_improvement_ge_5pct': brier_gain >= GATES['min_brier_improvement'],
                'improves_in_3_of_4_seasons': improving >= GATES['min_improving_seasons'],
                'log_loss_regression_le_2pct': ll_regression <= GATES['max_log_loss_regression'],
                'interval_favourable': upper < 0,
            }
            entry['all_gates_pass'] = all(entry['gates'].values())
        summary.append(entry)
    return {
        'status': 'retrospective_neutral_prior_proxy_not_promotion_eligible',
        'season_counts': season_counts, 'gates': GATES, 'candidates': summary,
        'limitations': [
            'Synthetic neutral priors/conference; not archived incumbent forecasts.',
            'FBS-vs-FBS games only; FCS games excluded from both arms.',
            'Final score eligibility assumes kickoff + four hours; publication time not verified.',
            'Candidate selection on 2022-2025 is exploratory; independent held-out validation required.',
            'No automatic model promotion, production ranking or forecast change.',
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': result['status'], 'season_counts': result['season_counts'],
                      'candidates': len(result['candidates'])}))


if __name__ == '__main__':
    main()
