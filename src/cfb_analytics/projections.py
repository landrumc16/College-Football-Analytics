"""Expected wins and conference wins from remaining schedule.

Matches Projections!S:V and Teams!AP,AQ,AS. Completed games must be
excluded from the remaining schedule.
"""
from dataclasses import dataclass
from collections import defaultdict
from .model import win_probability_from_rating_gap


@dataclass(frozen=True)
class ScheduledGame:
    home: str
    away: str
    completed: bool = False


@dataclass(frozen=True)
class TeamProjection:
    projected_wins: float
    remaining_win_variance: float
    projected_conference_wins: float
    remaining_games: int


def project_season(teams: dict[str, tuple[str, float, int, int]],
                   schedule: list[ScheduledGame], *,
                   home_field_advantage: float = 3.0,
                   win_probability_scale: float = 18.0,
                   fcs_rating: float = -26.0) -> dict[str, TeamProjection]:
    """teams maps name -> (conference, adaptive_rating, wins, conf_wins)."""
    remaining_wins = defaultdict(float)
    variances = defaultdict(float)
    conf_wins = defaultdict(float)
    counts = defaultdict(int)
    for game in schedule:
        if game.completed:
            continue
        if game.home == game.away:
            raise ValueError("Same home and away team")
        home_rating = teams[game.home][1] if game.home in teams else fcs_rating
        away_rating = teams[game.away][1] if game.away in teams else fcs_rating
        p_home = win_probability_from_rating_gap(
            home_rating - away_rating + home_field_advantage, win_probability_scale)
        is_conference = (game.home in teams and game.away in teams
                         and teams[game.home][0] == teams[game.away][0]
                         and teams[game.home][0] != "Independent")
        for name, p in ((game.home, p_home), (game.away, 1 - p_home)):
            if name not in teams:
                continue
            remaining_wins[name] += p
            variances[name] += p * (1 - p_home if name == game.home else p_home)
            counts[name] += 1
            if is_conference:
                conf_wins[name] += p
    return {
        name: TeamProjection(
            projected_wins=wins + remaining_wins[name],
            remaining_win_variance=variances[name],
            projected_conference_wins=conference_wins + conf_wins[name],
            remaining_games=counts[name],
        )
        for name, (_, _, wins, conference_wins) in teams.items()
    }
