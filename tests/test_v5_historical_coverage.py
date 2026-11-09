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
        "strength_complete": 1, "ap_complete": 1, "coaches_complete": 0
    }
    assert report["window_counts"]["3"]["strength_complete"] == 1
    partial = next(team for team in report["teams"] if team["team"] == "Partial")
    assert partial["windows"]["3"]["strength_missing"] == [2023, 2024]
    assert partial["windows"]["10"]["strength_complete"] is False


def test_empty_sources_do_not_claim_coverage():
    report = historical_coverage_inventory([], [], 2025)
    assert report["team_count"] == 0
    assert report["window_counts"]["10"]["strength_complete"] == 0
    assert report["publication_authorized"] is False
