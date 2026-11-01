import pytest
from cfb_analytics.model import ModelSettings
from cfb_analytics.ratings import Game, Team, calculate_ratings


def test_two_team_iteration_and_conference_shift():
    teams = [Team("A", "X", 10), Team("B", "Y", -10)]
    games = [Game("A", "B", 20, 10)]
    ratings = calculate_ratings(teams, games)
    # Adjusted margin is +7; first pass uses opponent's prior rating.
    assert ratings["A"].passes[1] == pytest.approx((-10 + 7 + 5 * 10) / 6)
    assert ratings["B"].passes[1] == pytest.approx((10 - 7 + 5 * -10) / 6)
    assert ratings["A"].wins == 1
    assert ratings["B"].losses == 1
    assert len(ratings["A"].passes) == 9
    assert ratings["A"].adaptive_rating == ratings["A"].passes[5]


def test_fcs_fallback():
    team = Team("A", "X", 0)
    result = calculate_ratings([team], [Game("A", "FCS", 30, 10)])
    assert result["A"].passes[1] == pytest.approx((-26 + 17) / 6)


def test_empty_schedule_remains_prior():
    result = calculate_ratings([Team("A", "X", 8)], [])
    assert result["A"].adaptive_rating == pytest.approx(8)
    assert result["A"].strength_of_schedule == 0


def test_no_duplicate_teams():
    with pytest.raises(ValueError):
        calculate_ratings([Team("A", "X", 0), Team("A", "Y", 0)], [])
