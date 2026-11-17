"""Research-only weighted counterpart to the workbook-parity rating engine.

Do not call from production pipeline. Input completed games must be sorted
chronologically by kickoff (not merely by week or provider game ID).
"""
from collections import defaultdict
from .model import ModelSettings, adjusted_home_margin
from .ratings import Team, Game
from .recency_research import team_game_weights


def calculate_weighted_ratings(teams: list[Team], games: list[Game],
                               settings: ModelSettings = ModelSettings(),
                               *, early: float = 1.0, middle: float = 1.5,
                               recent: float = 2.0) -> dict[str, float]:
    """Opponent-adjusted current strength with per-team rolling tier weights.

    Normalize weights to the team's game count to preserve the incumbent
    prior/ridge scale. Each game has a separate weight for each participant.
    """
    if settings.ridge_strength <= 0:
        raise ValueError("ridge_strength must be positive")
    names = {t.name for t in teams}
    if not names or len(names) != len(teams):
        raise ValueError("No teams or duplicate team names")
    for game in games:
        if game.home == game.away or game.home_score < 0 or game.away_score < 0:
            raise ValueError("Invalid completed game")
    conf = defaultdict(list)
    for t in teams:
        conf[t.conference].append(t.name)
    priors = {t.name: settings.prior_year_weight * t.prior for t in teams}
    weights = {}
    counts = {}
    for name in names:
        normalized = team_game_weights(games, name, early=early,
                                       middle=middle, recent=recent)
        counts[name] = len(normalized)
        weights[name] = {index: weight * counts[name]
                         for index, weight in normalized.items()}
    passes = [priors]
    for _ in range(8):
        previous = passes[-1]
        contributions = defaultdict(float)
        for i, game in enumerate(games):
            margin = adjusted_home_margin(game.home_score, game.away_score, settings)
            if game.home in names:
                contributions[game.home] += weights[game.home][i] * (
                    previous.get(game.away, settings.fcs_opponent_rating) + margin)
            if game.away in names:
                contributions[game.away] += weights[game.away][i] * (
                    previous.get(game.home, settings.fcs_opponent_rating) - margin)
        shifts = {}
        for conference, members in conf.items():
            shifts[conference] = (sum(previous[n] - priors[n] for n in members)
                                  / len(members))
        current = {}
        for t in teams:
            prior = priors[t.name] + settings.conference_shrink * shifts[t.conference]
            current[t.name] = (contributions[t.name] + settings.ridge_strength * prior) / (
                counts[t.name] + settings.ridge_strength)
        passes.append(current)
    completed = len(games)
    chosen = 5 if completed < 200 else 6 if completed < 400 else 7 if completed < 650 else 8
    return dict(passes[chosen])
