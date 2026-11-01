from cfb_analytics.parity import load_baseline


def test_complete_frozen_baseline():
    teams, games = load_baseline()
    assert len(teams) == 138
    assert len(games) == 510
    assert len({team["name"] for team in teams}) == 138
    assert all(isinstance(g["home_score"], (int, float)) for g in games)
