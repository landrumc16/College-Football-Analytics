import pytest
from cfb_analytics.cfp import simulate_cfp


def teams():
    return {f"T{i}": {"conference": f"C{i // 3}", "rating": 20-i,
                       "wins": 6, "conference_wins": 3} for i in range(15)}


def test_duplicate_reverse_matchup_rejected():
    with pytest.raises(ValueError, match="Duplicate remaining matchup"):
        simulate_cfp(teams(), [{"home": "T0", "away": "T1"},
                               {"home": "T1", "away": "T0"}], simulations=1)


def test_unmodeled_game_rejected():
    with pytest.raises(ValueError, match="no modeled FBS"):
        simulate_cfp(teams(), [{"home": "FCS1", "away": "FCS2"}], simulations=1)


@pytest.mark.parametrize("field,value", [("rating", float("nan")),
                                           ("rating", float("inf")),
                                           ("wins", -1), ("conference_wins", True)])
def test_invalid_team_state_rejected(field, value):
    fixture = teams()
    fixture["T0"][field] = value
    with pytest.raises(ValueError):
        simulate_cfp(fixture, [], simulations=1)


def test_legitimate_fcs_game_preserved():
    result = simulate_cfp(teams(), [{"home": "FCS", "away": "T0"}], simulations=2)
    assert result["simulations"] == 2
