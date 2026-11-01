"""Workbook-parity iterative opponent-adjusted team rating engine.

Passes 1..8 correspond to Teams columns G,H,I,J,K,Q,R,S.
Games are supplied only when completed. Neutral-site handling follows the
observed Games!G formula (home advantage always removed).
"""
from collections import defaultdict
from dataclasses import dataclass
from .model import ModelSettings, adjusted_home_margin


@dataclass(frozen=True)
class Team:
    name: str
    conference: str
    prior: float


@dataclass(frozen=True)
class Game:
    home: str
    away: str
    home_score: int
    away_score: int
    week: int = 0


@dataclass(frozen=True)
class TeamRating:
    team: str
    games: int
    wins: int
    losses: int
    passes: tuple[float, ...]
    adaptive_rating: float
    strength_of_schedule: float
    quality_wins: int
    bad_losses: int


def calculate_ratings(teams: list[Team], games: list[Game],
                      settings: ModelSettings = ModelSettings()) -> dict[str, TeamRating]:
    if settings.ridge_strength <= 0:
        raise ValueError("ridge_strength must be positive")
    by_name = {team.name: team for team in teams}
    if len(by_name) != len(teams):
        raise ValueError("Duplicate team names")
    if not by_name:
        raise ValueError("No teams")
    conf_members = defaultdict(list)
    for team in teams:
        conf_members[team.conference].append(team.name)
    counts = defaultdict(int)
    wins = defaultdict(int)
    losses = defaultdict(int)
    for game in games:
        if game.home == game.away:
            raise ValueError("Same home and away team")
        if game.home_score < 0 or game.away_score < 0:
            raise ValueError("Negative score")
        for name in (game.home, game.away):
            if name in by_name:
                counts[name] += 1
        if game.home_score > game.away_score:
            wins[game.home] += 1
            losses[game.away] += 1
        elif game.home_score < game.away_score:
            wins[game.away] += 1
            losses[game.home] += 1

    priors = {t.name: settings.prior_year_weight * t.prior for t in teams}
    passes = [priors]
    for _ in range(8):
        previous = passes[-1]
        contributions = defaultdict(float)
        for game in games:
            margin = adjusted_home_margin(game.home_score, game.away_score, settings)
            if game.home in by_name:
                contributions[game.home] += previous.get(game.away, settings.fcs_opponent_rating) + margin
            if game.away in by_name:
                contributions[game.away] += previous.get(game.home, settings.fcs_opponent_rating) - margin
        conf_shift = {}
        for conference, names in conf_members.items():
            current_average = sum(previous[n] for n in names) / len(names)
            initial_average = sum(priors[n] for n in names) / len(names)
            conf_shift[conference] = current_average - initial_average
        current = {}
        for team in teams:
            prior = priors[team.name] + settings.conference_shrink * conf_shift[team.conference]
            current[team.name] = (contributions[team.name] + settings.ridge_strength * prior) / (
                counts[team.name] + settings.ridge_strength
            )
        passes.append(current)

    completed = len(games)
    chosen_pass = 5 if completed < 200 else 6 if completed < 400 else 7 if completed < 650 else 8
    final = passes[chosen_pass]
    output = {}
    for team in teams:
        opponents = []
        quality_wins = 0
        bad_losses = 0
        for game in games:
            if team.name not in (game.home, game.away):
                continue
            is_home = team.name == game.home
            opponent = game.away if is_home else game.home
            opp_rating = passes[8].get(opponent, settings.fcs_opponent_rating)
            opponents.append(opp_rating)
            margin = game.home_score - game.away_score
            team_margin = margin if is_home else -margin
            if team_margin > 0 and opp_rating > 0:
                quality_wins += 1
            if team_margin < 0 and opp_rating < 0:
                bad_losses += 1
        output[team.name] = TeamRating(
            team=team.name, games=counts[team.name], wins=wins[team.name],
            losses=losses[team.name],
            passes=tuple(p[team.name] for p in passes),
            adaptive_rating=final[team.name],
            strength_of_schedule=sum(opponents) / len(opponents) if opponents else 0.0,
            quality_wins=quality_wins, bad_losses=bad_losses,
        )
    return output
