"""Research blend behavior and leakage boundaries."""
import pytest
from scripts.strength_blend_research import blend_strength, momentum_window


def test_default_blend():
    r = blend_strength(82, 94, momentum_games=3)
    assert r.combined_strength == pytest.approx(86.2)
    assert r.season_weight == pytest.approx(.65)
    assert r.direction == "rising"


def test_momentum_only_latest_three_or_four():
    games = list(range(1, 11))
    assert momentum_window(games) == [8, 9, 10]
    assert momentum_window(games, window=4) == [7, 8, 9, 10]


def test_no_early_season_double_count_claim():
    r = blend_strength(82, None, momentum_games=2)
    assert r.combined_strength == 82
    assert r.momentum_weight == 0
    assert r.direction == "insufficient_data"


def test_declining_and_steady():
    assert blend_strength(85, 75, momentum_games=4).direction == "declining"
    assert blend_strength(85, 85, momentum_games=3).direction == "steady"


@pytest.mark.parametrize("weight", [-.1, 1.1])
def test_reject_invalid_weights(weight):
    with pytest.raises(ValueError):
        blend_strength(80, 90, momentum_games=3, momentum_weight=weight)


def test_reject_missing_full_window():
    with pytest.raises(ValueError):
        blend_strength(80, None, momentum_games=3)


def test_reject_invalid_window():
    with pytest.raises(ValueError):
        momentum_window([1, 2, 3], window=5)


def test_opponent_adjusted_components_use_only_latest_three():
    from cfb_analytics.ratings import Team, Game
    from scripts.strength_blend_research import calculate_strength_components
    teams = [Team("A", "X", 0), Team("B", "X", 0)]
    games = [
        Game("A", "B", 10, 20, 1),
        Game("A", "B", 10, 20, 2),
        Game("A", "B", 30, 10, 3),
        Game("A", "B", 30, 10, 4),
        Game("A", "B", 30, 10, 5),
    ]
    values = calculate_strength_components(teams, games)
    assert values["A"].momentum_games == 3
    assert values["A"].recent_momentum > values["A"].season_strength
    assert values["A"].combined_strength > values["A"].season_strength
    assert values["B"].recent_momentum < values["B"].season_strength


def test_four_game_window_requires_four_completed_games():
    from cfb_analytics.ratings import Team, Game
    from scripts.strength_blend_research import calculate_strength_components
    teams = [Team("A", "X", 0), Team("B", "X", 0)]
    games = [Game("A", "B", 21, 10, i) for i in (1, 2, 3)]
    values = calculate_strength_components(teams, games, window=4)
    assert values["A"].momentum_games == 3
    assert values["A"].recent_momentum is None
    assert values["A"].combined_strength == values["A"].season_strength
