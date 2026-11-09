import json

from cfb_analytics.v4_program_intelligence import build_program_intelligence


def test_shared_team_and_comparison_contract_is_serializable():
    strength = [
        dict(team=team, season=year, strength=score, source=f"verified-{year}")
        for team, score in (("A", 10), ("B", 5))
        for year in range(2016, 2026)
    ]
    polls = [
        dict(team="A", season=year, poll="AP", preseason_rank=5,
             final_rank=10, source=f"ap-{year}")
        for year in range(2016, 2026)
    ]
    report = build_program_intelligence(strength, polls, 2025)
    programs = {p["team"]: p for p in report["programs"]}
    assert programs["A"]["program_rankings"]["10"]["rank"] == 1
    assert programs["B"]["program_rankings"]["10"]["rank"] == 2
    assert programs["A"]["trajectory"]["long_term"]["classification"] == "stable"
    assert programs["A"]["trajectory"]["medium_term"]["classification"] == "stable"
    assert programs["A"]["hype"]["AP"]["dropped_out"] == 0
    assert programs["B"]["hype"] == {}
    assert report["predictive_validation"] is False
    assert json.loads(json.dumps(report))["schema_version"] == 1


def test_poll_only_team_keeps_missing_strength_as_missing():
    polls = [dict(team="C", season=2025, poll="Coaches",
                  preseason_rank=None, final_rank=22, source="poll-2025")]
    report = build_program_intelligence([], polls, 2025)
    team = report["programs"][0]
    assert team["program_rankings"] is None
    assert team["trajectory"] is None
    assert team["hype"]["Coaches"]["entered_top25"] == 1


def test_chart_series_uses_only_original_sourced_seasons_and_preserves_gaps():
    strength = [
        dict(team="A", season=2022, strength=2.5, source="verified-2022"),
        dict(team="A", season=2024, strength=6.0, source="verified-2024"),
    ]
    report = build_program_intelligence(strength, [], 2025)
    series = report["programs"][0]["season_strength_history"]
    assert series == [
        {"season": 2022, "strength": 2.5, "source": "verified-2022"},
        {"season": 2024, "strength": 6.0, "source": "verified-2024"},
    ]
    assert report["programs"][0]["trajectory"]["recent"]["classification"] == "insufficient_data"
    assert report["programs"][0]["trajectory"]["medium_term"]["classification"] == "insufficient_data"
