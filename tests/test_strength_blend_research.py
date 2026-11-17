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


def test_momentum_is_plain_mean_of_latest_window_with_as_of_opponent_benchmark():
    from types import SimpleNamespace
    from cfb_analytics.ratings import Team, Game
    from scripts.strength_blend_research import calculate_strength_components
    teams = [Team("A", "X", 0), Team("B", "X", 0), Team("C", "X", 0)]
    ratings = {"A": SimpleNamespace(adaptive_rating=6.0), "B": SimpleNamespace(adaptive_rating=2.0),
               "C": SimpleNamespace(adaptive_rating=-4.0)}
    games = [Game("A", "B", 0, 50, 1), Game("C", "A", 10, 20, 2), Game("A", "FCS U", 40, 10, 3), Game("A", "B", 24, 21, 4)]
    a = calculate_strength_components(teams, games, window=3, momentum_weight=0.2, season_ratings=ratings)["A"]
    # away at C: -(10-20-3)=13 + (-4) = 9; home vs FCS: 27 + (-26) = 1; home vs B: 0 + 2 = 2 (week 1 excluded)
    assert a.recent_momentum == pytest.approx((9 + 1 + 2) / 3)
    assert a.combined_strength == pytest.approx(0.8 * 6 + 0.2 * 4)
    assert a.direction == "steady"                              # -2 points is within the +/-7 steady band
    changed = [Game("A", "B", 70, 0, 1)] + games[1:]           # a different pre-window result
    b = calculate_strength_components(teams, changed, window=3, momentum_weight=0.2, season_ratings=ratings)["A"]
    assert b.recent_momentum == pytest.approx(a.recent_momentum)


def test_steady_band_and_zero_weight_parity():
    assert blend_strength(10.0, 16.9, momentum_games=3).direction == "steady"      # +/-7: about 1 SD of recent-vs-season
    assert blend_strength(10.0, 17.1, momentum_games=3).direction == "rising"
    assert blend_strength(10.0, 2.9, momentum_games=3).direction == "declining"
    assert blend_strength(10.0, 3.1, momentum_games=3).direction == "steady"
    assert blend_strength(10.0, 30.0, momentum_games=3, momentum_weight=0.0).combined_strength == 10.0
