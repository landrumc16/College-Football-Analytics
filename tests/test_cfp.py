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
    assert sum(x["quarterfinal"] for x in a["teams"]) == 8
    assert sum(x["semifinal"] for x in a["teams"]) == 4
    assert sum(x["final"] for x in a["teams"]) == 2
    assert abs(sum(x["national_title"] for x in a["teams"]) - 1) < 0.01
    assert all(0 <= x["national_title"] <= x["cfp_field"] <= 1 for x in a["teams"])


def test_cfp_favors_stronger_team():
    teams = {f"T{i}": {"conference": f"C{i // 3}", "rating": 30-i*3,
                        "wins": 8, "conference_wins": 4} for i in range(15)}
    result = simulate_cfp(teams, [], simulations=1000, seed=11)
    odds = {x["team"]: x["national_title"] for x in result["teams"]}
    assert odds["T0"] > odds["T14"]

def test_season_win_ranges_and_bowl_probabilities():
    teams = {f"T{i}": {"conference": f"C{i // 3}", "rating": 15-i,
                        "wins": 6, "conference_wins": 3} for i in range(15)}
    result = simulate_cfp(teams, [{"home": "T0", "away": "T1", "neutral_site": False}], simulations=100, seed=1)
    for team in result["teams"]:
        assert team["wins_p10"] <= team["average_wins"] <= team["wins_p90"]
        assert 0 <= team["bowl_eligible"] <= 1
    assert all(team["bowl_eligible"] == 1 for team in result["teams"])


def test_conference_championship_matchups_and_title_totals():
    teams = {
        f"T{i}": {"conference": f"C{i // 3}", "rating": 25 - i,
                  "wins": 7, "conference_wins": 4}
        for i in range(15)
    }
    result = simulate_cfp(teams, [], simulations=100, seed=2026)
    assert len(result["conference_championships"]) == 5
    assert all(len(c["most_common_matchup"]) == 2 for c in result["conference_championships"])
    assert all(c["matchup_probability"] == 1 for c in result["conference_championships"])
    assert sum(row["conference_title"] for row in result["teams"]) == 5
