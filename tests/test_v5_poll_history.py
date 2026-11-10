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


def test_unmapped_team_rejected():
    snapshots, mapping = fixture()
    del mapping["26"]
    with pytest.raises(ValueError, match="unmapped team ID"):
        build_poll_history(snapshots, mapping, 2024, 2025)


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
