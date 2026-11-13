import pytest

from scripts.resolve_v5_espn_team_ids import candidate_mapping, directory_id_names


def test_directory_identity_resolution_preserves_existing_canonical_names():
    directory = {"sports": [{"leagues": [{"teams": [
        {"team": {"id": "61", "displayName": "Georgia Bulldogs"}},
        {"team": {"id": "2", "displayName": "Auburn Tigers"}},
    ]}]}]}
    snapshots = [{"snapshots": {"ap_preseason": [
        {"team_id": "61", "rank": 1},
        {"team_id": "2", "rank": 2},
        {"team_id": "999", "rank": 3},
    ]}}]
    result = candidate_mapping(snapshots, directory, {"61": "Georgia"})
    assert result["publishable"] is False
    assert result["mapping"]["61"] == "Georgia"
    assert result["mapping"]["2"] == "Auburn Tigers"
    assert result["unresolved_ids"] == ["999"]
    assert result["ranked_ids"] == 3


def test_conflicting_directory_id_rejected():
    payload = {"sports": [{"leagues": [{"teams": [
        {"team": {"id": "2", "displayName": "Auburn"}},
        {"team": {"id": "2", "displayName": "Another"}},
    ]}]}]}
    with pytest.raises(ValueError, match="Conflicting ESPN identity"):
        directory_id_names(payload)


def test_candidate_flags_duplicate_names_for_manual_resolution():
    directory = {"sports": [{"leagues": [{"teams": [
        {"team": {"id": "2", "displayName": "Same"}},
        {"team": {"id": "3", "displayName": "Same"}},
    ]}]}]}
    snapshots = [{"snapshots": {"ap_final": [
        {"team_id": "2", "rank": 1},
        {"team_id": "3", "rank": 2},
    ]}}]
    result = candidate_mapping(snapshots, directory, {})
    assert result["duplicate_canonical_names"] == {"Same": ["2", "3"]}


def test_canonical_reconciliation_uses_school_location_not_mascot():
    directory = {"sports": [{"leagues": [{"teams": [
        {"team": {"id": "61", "displayName": "Georgia Bulldogs", "location": "Georgia"}},
        {"team": {"id": "2", "displayName": "Auburn Tigers", "location": "Auburn"}},
    ]}]}]}
    snapshots = [{"snapshots": {"ap_preseason": [
        {"team_id": "61", "rank": 1},
        {"team_id": "2", "rank": 2},
    ]}}]
    result = candidate_mapping(snapshots, directory, {},
                               canonical_teams={"Georgia", "Auburn"})
    assert result["mapping"] == {"2": "Auburn", "61": "Georgia"}
    assert result["unresolved_ids"] == []
