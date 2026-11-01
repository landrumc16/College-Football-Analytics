import pytest
from cfb_analytics.projections import ScheduledGame, project_season


def test_remaining_game_projections_are_symmetric():
    teams = {"A": ("ACC", 10, 4, 2), "B": ("ACC", 10, 3, 1)}
    result = project_season(teams, [ScheduledGame("A", "B")])
    p = result["A"].projected_wins - 4
    assert p > 0.5  # home-field advantage
    assert result["B"].projected_wins == pytest.approx(3 + 1 - p)
    assert result["A"].remaining_win_variance == pytest.approx(p * (1 - p))
    assert result["A"].projected_conference_wins == pytest.approx(2 + p)


def test_completed_games_do_not_count_twice():
    teams = {"A": ("ACC", 10, 4, 2)}
    result = project_season(teams, [ScheduledGame("A", "FCS", completed=True)])
    assert result["A"].projected_wins == 4
    assert result["A"].remaining_games == 0


def test_independents_are_not_conference_games():
    teams = {"A": ("Independent", 5, 1, 0), "B": ("Independent", 0, 1, 0)}
    result = project_season(teams, [ScheduledGame("A", "B")])
    assert result["A"].projected_conference_wins == 0
