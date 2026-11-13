"""V5 coverage inventory fixtures: descriptive, never an attestation."""
from cfb_analytics.v5_historical_coverage import historical_coverage_inventory


def strength(year, team="Example"):
    return {"team": team, "season": year, "strength": 2.0, "source": "https://example.org/strength"}


def poll(year, name="AP", team="Example"):
    return {"team": team, "season": year, "poll": name, "preseason_rank": None,
            "final_rank": 15, "source": "https://example.org/polls"}


def test_complete_and_partial_windows_are_reported_separately():
    report = historical_coverage_inventory(
        [strength(y) for y in range(2016, 2026)] + [strength(2025, "Partial")],
        [poll(y) for y in range(2016, 2026)] + [poll(2025, "Coaches")],
        2025,
    )
    assert report["status"] == "coverage_inventory_not_source_attestation"
    assert report["publication_authorized"] is False
    assert report["window_counts"]["10"] == {
        "strength_complete": 1, "ap_complete": 1, "coaches_complete": 0,
        "strength_and_both_polls_complete": 0
    }
    assert report["window_counts"]["3"]["strength_complete"] == 1
    assert report["teams"][0]["strength_sources"] or report["teams"][1]["strength_sources"]
    example = next(team for team in report["teams"] if team["team"] == "Example")
    assert example["strength_sources"][0] == {"season": 2016, "source": "https://example.org/strength"}
    assert example["poll_sources"]["AP"][0]["season"] == 2016
    assert example["windows"]["10"]["strength_and_both_polls_complete"] is False
    partial = next(team for team in report["teams"] if team["team"] == "Partial")
    assert partial["windows"]["3"]["strength_missing"] == [2023, 2024]
    assert partial["windows"]["10"]["strength_complete"] is False


def test_empty_sources_do_not_claim_coverage():
    report = historical_coverage_inventory([], [], 2025)
    assert report["team_count"] == 0
    assert report["window_counts"]["10"]["strength_complete"] == 0
    assert report["publication_authorized"] is False


def test_joint_complete_window_requires_both_independent_poll_series():
    report = historical_coverage_inventory(
        [strength(y) for y in range(2016, 2026)],
        [poll(y, name) for y in range(2016, 2026) for name in ("AP", "Coaches")],
        2025,
    )
    assert report["window_counts"]["10"]["strength_and_both_polls_complete"] == 1
    assert report["teams"][0]["windows"]["10"]["strength_and_both_polls_complete"] is True
