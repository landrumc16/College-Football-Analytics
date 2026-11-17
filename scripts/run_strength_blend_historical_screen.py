"""Retrospective season/momentum blend screen; NEVER production promotion evidence.

Uses the verified FBS results archive, neutral priors and a synthetic conference.
No season-specific historical incumbent priors or archived pregame forecasts exist.
Candidate weights are descriptive research, not tuned production parameters.
"""
import argparse
import gzip
import json
from datetime import timedelta
from pathlib import Path
from cfb_analytics.ratings import Team, Game, calculate_ratings
from cfb_analytics.predictions import predict
from cfb_analytics.model import ModelSettings
from cfb_analytics.recency_replay_research import _utc, paired_metrics
from scripts.strength_blend_research import calculate_strength_components

ROOT = Path(__file__).resolve().parents[1]
SEASONS = (2022, 2023, 2024, 2025)
DISPUTED = {'401014983', '401021686', '401309645'}
WEIGHTS = (0.0, 0.2, 0.3, 0.35, 0.4, 0.5)


def run():
    with gzip.open(ROOT / 'research/archive/verified/espn-games.json.gz',
                   'rt', encoding='utf-8') as fh:
        archive = json.load(fh)
    settings = ModelSettings()
    all_rows = {(window, weight): [] for window in (3, 4) for weight in WEIGHTS}
    season_counts = {}
    for season in SEASONS:
        records = [g for g in archive[str(season)]
                   if g.get('fbs_game') is True
                   and str(g['game_id']) not in DISPUTED]
        records.sort(key=lambda g: (_utc(g.get('kickoff') or g.get('start_date')),
                                    str(g['game_id'])))
        names = sorted({g[k] for g in records for k in ('home', 'away')})
        teams = [Team(n, 'Neutral research pool', 0.0) for n in names]
        parsed = [(_utc(g.get('kickoff') or g.get('start_date')), g) for g in records]
        season_counts[str(season)] = len(parsed)
        for kickoff, target in parsed:
            eligible = [g for dt, g in parsed
                        if dt + timedelta(hours=4) < kickoff]
            games = [Game(g['home'], g['away'], g['home_score'],
                          g['away_score'], int(g['week'])) for g in eligible]
            base = calculate_ratings(teams, games, settings)
            for window in (3, 4):
                # Calculate as-of strength ONCE per window, then vary only blend weights.
                components = calculate_strength_components(
                    teams, games, window=window, momentum_weight=1.0, settings=settings)
                for weight in WEIGHTS:
                    def rating(name):
                        if name not in components:
                            return settings.fcs_opponent_rating
                        c = components[name]
                        return (1 - weight) * c.season_strength + weight * (
                            c.recent_momentum if c.recent_momentum is not None
                            else c.season_strength)
                    args = dict(neutral=bool(target.get('neutral_site', False)),
                                home_field_advantage=settings.home_field_advantage,
                                model_scale=settings.win_probability_scale)
                    forecast = predict(target['home'], target['away'],
                                       rating(target['home']), rating(target['away']),
                                       **args)
                    incumbent = predict(target['home'], target['away'],
                                        base[target['home']].adaptive_rating,
                                        base[target['away']].adaptive_rating, **args)
                    all_rows[(window, weight)].append({
                        'season': season, 'week': int(target['week']),
                        'game_id': str(target['game_id']),
                        'home_won': int(target['home_score'] > target['away_score']),
                        'incumbent_probability': incumbent.model_home_probability,
                        'challenger_probability': forecast.model_home_probability,
                        'incumbent_margin': incumbent.home_margin,
                        'challenger_margin': forecast.home_margin,
                        'actual_margin': target['home_score'] - target['away_score'],
                    })
    summary = []
    for (window, weight), rows in all_rows.items():
        metrics = paired_metrics(rows)
        by_season = {}
        for season in SEASONS:
            subset = [r for r in rows if r['season'] == season]
            by_season[str(season)] = paired_metrics(subset)
        summary.append({'window': window, 'momentum_weight': weight,
                        'paired_games': len(rows), 'metrics': metrics,
                        'by_season': by_season})
    return {
        'status': 'retrospective_neutral_prior_proxy_not_promotion_eligible',
        'season_counts': season_counts,
        'candidates': summary,
        'limitations': [
            'Synthetic neutral priors/conference; not archived incumbent forecasts.',
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
    print(json.dumps({'status': result['status'],
                      'season_counts': result['season_counts'],
                      'candidates': len(result['candidates'])}))


if __name__ == '__main__':
    main()
