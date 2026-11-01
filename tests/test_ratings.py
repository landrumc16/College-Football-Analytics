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



def test_fcs_away_result_counts_for_fbs_rating_and_record():
    """An FCS home game must contribute to the FBS visitor's rating."""
    ratings = calculate_ratings(
        [Team("FBS", "X", 0)], [Game("FCS Opponent", "FBS", 7, 28)])
    # Home adjusted margin = 7 - 28 - 3 = -24;
    # FBS away contribution = -26 - (-24) = -2.
    assert ratings["FBS"].passes[1] == pytest.approx(-2 / 6)
    assert ratings["FBS"].wins == 1
    assert ratings["FBS"].games == 1
    assert "FCS Opponent" not in ratings


def test_fcs_blowout_is_capped_before_rating_update():
    ratings = calculate_ratings(
        [Team("FBS", "X", 0)], [Game("FBS", "FCS Opponent", 100, 0)])
    assert ratings["FBS"].passes[1] == pytest.approx((-26 + 45) / 6)
    assert ratings["FBS"].strength_of_schedule == pytest.approx(-26)
    assert ratings["FBS"].wins == 1


def test_fcs_loss_counts_against_fbs_team():
    ratings = calculate_ratings(
        [Team("FBS", "X", 0)], [Game("FBS", "FCS Opponent", 10, 17)])
    assert ratings["FBS"].passes[1] == pytest.approx((-26 - 10) / 6)
    assert ratings["FBS"].losses == 1
    assert ratings["FBS"].bad_losses == 1
