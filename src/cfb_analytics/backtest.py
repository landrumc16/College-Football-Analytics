"""Leakage-free chronological evaluation of the rating model.

Each game is predicted using only results from earlier weeks. Games within
the same week are predicted from the same pre-week snapshot.
"""
from math import log

from .model import ModelSettings, win_probability_from_rating_gap
from .ratings import Game, Team, calculate_ratings


def backtest_weeks(teams: list[Team], games: list[Game],
                   settings: ModelSettings = ModelSettings()) -> dict:
    if not teams:
        raise ValueError("At least one team is required")
    if any(g.week <= 0 for g in games):
        raise ValueError("Every historical game needs a positive week")
    known = {team.name for team in teams}
    if len(known) != len(teams):
        raise ValueError("Duplicate team names")
    history = []
    scored = []
    for week in sorted({game.week for game in games}):
        ratings = calculate_ratings(teams, history, settings)
        for game in (g for g in games if g.week == week):
            if game.home not in known and game.away not in known:
                continue
            home = (ratings[game.home].adaptive_rating if game.home in known
                    else settings.fcs_opponent_rating)
            away = (ratings[game.away].adaptive_rating if game.away in known
                    else settings.fcs_opponent_rating)
            gap = home - away + settings.home_field_advantage
            probability = win_probability_from_rating_gap(
                gap, settings.win_probability_scale)
            actual = int(game.home_score > game.away_score)
            if game.home_score == game.away_score:
                raise ValueError("Historical completed games cannot be tied")
            prior_home = (settings.prior_year_weight * next(
                (t.prior for t in teams if t.name == game.home),
                settings.fcs_opponent_rating))
            prior_away = (settings.prior_year_weight * next(
                (t.prior for t in teams if t.name == game.away),
                settings.fcs_opponent_rating))
            baseline = win_probability_from_rating_gap(
                prior_home - prior_away + settings.home_field_advantage,
                settings.win_probability_scale)
            scored.append((probability, baseline, actual))
        history.extend(g for g in games if g.week == week)
    if not scored:
        return {"games": 0, "model": None, "preseason_baseline": None}

    def metrics(index):
        probabilities = [row[index] for row in scored]
        n = len(scored)
        return {
            "winner_accuracy": sum((p >= 0.5) == bool(y)
                                   for p, (_, _, y) in zip(probabilities, scored)) / n,
            "brier_score": sum((p - y) ** 2
                               for p, (_, _, y) in zip(probabilities, scored)) / n,
            "log_loss": -sum(y * log(max(1e-15, p)) +
                             (1-y) * log(max(1e-15, 1-p))
                             for p, (_, _, y) in zip(probabilities, scored)) / n,
        }
    return {"games": len(scored), "model": metrics(0),
            "preseason_baseline": metrics(1)}
