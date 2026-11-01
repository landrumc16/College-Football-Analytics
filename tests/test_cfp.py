from cfb_analytics.cfp import simulate_cfp


def test_cfp_simulation_deterministic_and_probabilities():
    teams = {
        f"Team {i}": {"conference": f"League {i // 3}", "rating": 25 - i,
                      "wins": 8, "conference_wins": 5}
        for i in range(15)
    }
    a = simulate_cfp(teams, [], simulations=100, seed=42)
    b = simulate_cfp(teams, [], simulations=100, seed=42)
    assert a == b
    assert a["simulations"] == 100
    assert sum(x["cfp_field"] for x in a["teams"]) == 12
    assert sum(x["first_round_bye"] for x in a["teams"]) == 4
    assert abs(sum(x["national_title"] for x in a["teams"]) - 1) < 1e-9
    assert all(0 <= x["national_title"] <= x["cfp_field"] <= 1 for x in a["teams"])


def test_cfp_favors_stronger_team():
    teams = {f"T{i}": {"conference": f"C{i // 3}", "rating": 30-i*3,
                        "wins": 8, "conference_wins": 4} for i in range(15)}
    result = simulate_cfp(teams, [], simulations=1000, seed=11)
    odds = {x["team"]: x["national_title"] for x in result["teams"]}
    assert odds["T0"] > odds["T14"]
