import pytest
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
    assert sum(x["semifinal"] for x in a["teams"]) == pytest.approx(4)
    assert sum(x["final"] for x in a["teams"]) == pytest.approx(2)
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
    # Five simulated title games add exactly five wins per season.
    assert sum(row["average_wins"] for row in result["teams"]) == pytest.approx(15 * 7 + 5)



def test_cfp_seed_distribution_and_input_validation():
    import pytest
    teams = {f"T{i}": {"conference": f"C{i // 3}", "rating": 30-i,
                        "wins": 8, "conference_wins": 4} for i in range(15)}
    report = simulate_cfp(teams, [], simulations=200, seed=42)
    selected = [row for row in report["teams"] if row["cfp_field"] > 0]
    assert all(1 <= row["most_likely_seed"] <= 12 for row in selected)
    assert all(1 <= row["average_seed_when_selected"] <= 12 for row in selected)
    assert all(row["most_likely_seed"] is None for row in report["teams"] if row["cfp_field"] == 0)
    with pytest.raises(ValueError):
        simulate_cfp(teams, [{"home": "T1", "away": "T1"}], simulations=10)
    with pytest.raises(ValueError):
        simulate_cfp({}, [], simulations=10)
    with pytest.raises(ValueError):
        simulate_cfp(teams, [], simulations=0)


def test_non_fbs_only_games_do_not_change_fbs_cfp_outcomes():
    teams = {f"T{i}": {"conference": f"C{i // 3}", "rating": 30-i,
                        "wins": 8, "conference_wins": 4} for i in range(15)}
    fbs_game = {"home": "T0", "away": "FCS Opponent", "neutral_site": False}
    non_fbs_game = {"home": "FCS A", "away": "FCS B", "neutral_site": False}
    baseline = simulate_cfp(teams, [fbs_game], simulations=100, seed=31)
    with_non_fbs = simulate_cfp(teams, [fbs_game, non_fbs_game], simulations=100, seed=31)
    assert with_non_fbs == baseline


def test_duplicate_fcs_only_fixtures_do_not_block_live_report():
    teams = {f"T{i}": {"conference": f"C{i // 3}", "rating": 30-i,
                        "wins": 8, "conference_wins": 4} for i in range(15)}
    fcs_only = {"home": "Kean", "away": "The College of New Jersey"}
    expected = simulate_cfp(teams, [], simulations=10, seed=19)
    actual = simulate_cfp(teams, [fcs_only, fcs_only], simulations=10, seed=19)
    assert actual == expected
