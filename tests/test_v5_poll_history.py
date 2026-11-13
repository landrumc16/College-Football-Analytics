import pytest

from scripts.build_v5_poll_history import build_poll_history


def fixture():
    snapshots = []
    for year in (2024, 2025):
        snapshots.append({
            "season": year,
            "source_url": "https://example.org/polls.csv",
            "source_sha256": "a" * 64,
            "snapshots": {
                f"{poll}_{phase}": [
                    {"team_id": str(rank + (1 if phase == "final" else 0)), "rank": rank}
                    for rank in range(1, 26)
                ]
                for poll in ("ap", "coaches") for phase in ("preseason", "final")
            },
        })
    mapping = {str(i): f"Team {i}" for i in range(1, 27)}
    return snapshots, mapping


def test_unranked_finishes_and_new_entries_preserved():
    snapshots, mapping = fixture()
    rows = build_poll_history(snapshots, mapping, 2024, 2025)
    assert len(rows) == 104
    by_key = {(r["team"], r["season"], r["poll"]): r for r in rows}
    assert by_key[("Team 1", 2024, "AP")]["preseason_rank"] == 1
    assert by_key[("Team 1", 2024, "AP")]["final_rank"] is None
    assert by_key[("Team 26", 2025, "Coaches")]["preseason_rank"] is None
    assert by_key[("Team 26", 2025, "Coaches")]["final_rank"] == 25


def test_missing_year_rejected():
    snapshots, mapping = fixture()
    with pytest.raises(ValueError, match="every requested season"):
        build_poll_history(snapshots[:1], mapping, 2024, 2025)


def test_cohort_subset_does_not_require_mapping_all_ranked_teams():
    snapshots, mapping = fixture()
    mapping = {"1": "Team 1", "26": "Team 26"}
    rows = build_poll_history(snapshots, mapping, 2024, 2025)
    assert len(rows) == 8
    assert {r["team"] for r in rows} == {"Team 1", "Team 26"}


def test_duplicate_rank_rejected():
    snapshots, mapping = fixture()
    snapshots[0]["snapshots"]["ap_final"][0]["rank"] = 2
    with pytest.raises(ValueError, match="invalid top 25"):
        build_poll_history(snapshots, mapping, 2024, 2025)


def test_duplicate_canonical_identity_rejected():
    snapshots, mapping = fixture()
    mapping["26"] = mapping["25"]
    with pytest.raises(ValueError, match="unique"):
        build_poll_history(snapshots, mapping, 2024, 2025)


def test_unranked_both_endpoints_remains_in_full_cohort():
    snapshots, mapping = fixture()
    mapping["27"] = "Team 27"
    rows = build_poll_history(snapshots, mapping, 2024, 2025)
    assert len(rows) == 108
    absent = [r for r in rows if r["team"] == "Team 27"]
    assert len(absent) == 4
    assert all(r["preseason_rank"] is None and r["final_rank"] is None for r in absent)


def test_national_conversion_rejects_unmapped_ranked_teams():
    snapshots, mapping = fixture()
    with pytest.raises(ValueError, match="unmapped ranked team IDs"):
        build_poll_history(snapshots, {"1": "Team 1"}, 2024, 2025,
                           require_ranked_ids_mapped=True)


def test_national_conversion_accepts_complete_ranked_mapping():
    snapshots, mapping = fixture()
    rows = build_poll_history(snapshots, mapping, 2024, 2025,
                              require_ranked_ids_mapped=True)
    assert len(rows) == 104


def test_tied_competition_rankings_are_valid_in_national_conversion():
    snapshots, mapping = fixture()
    final = snapshots[0]["snapshots"]["ap_final"]
    final[7]["rank"] = 7
    final[6]["rank"] = 7
    final[8]["rank"] = 9
    rows = build_poll_history(snapshots, mapping, 2024, 2025,
                              require_ranked_ids_mapped=True)
    ranks = {r["team"]: r["final_rank"] for r in rows if r["season"] == 2024 and r["poll"] == "AP"}
    assert ranks["Team 8"] == 7
    assert ranks["Team 9"] == 7
