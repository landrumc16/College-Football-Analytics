from scripts.build_v5_historical_research import prepare


def test_research_keeps_unmapped_ids_and_unverified_trajectories():
    years = range(2016, 2026)
    records = {
        "seasons": [
            {"season": year, "teams": [
                {"team": "Example", "fbs_wins": 7, "fbs_losses": 5}
            ]}
            for year in years
        ]
    }
    snapshots = [
        {
            "season": year,
            "source_url": "https://example.org/poll",
            "source_sha256": "a" * 64,
            "snapshots": {
                f"{poll}_{phase}": [
                    {"team_id": str(i), "rank": i}
                    for i in range(1, 26)
                ]
                for poll in ("ap", "coaches")
                for phase in ("preseason", "final")
            },
        }
        for year in years
    ]
    result = prepare(
        records, snapshots, {"1": "Example"},
        latest_completed_season=2025,
        source="https://example.org/schedules",
    )
    assert result["publishable"] is False
    assert result["coverage"]["trajectory_complete_programs"] == 1
    assert result["coverage"]["unmapped_ranked_espn_ids"] == 24
    assert len(result["unmapped_ranked_team_ids"]["2"]) == 40
    assert result["trajectory"]["Example"]["verified"] is False
    assert len(result["poll_history"]) == 20
