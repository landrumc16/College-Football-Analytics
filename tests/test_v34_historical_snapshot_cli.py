import pytest
from cfb_analytics.v34_historical_snapshot_cli import collect_snapshot


def test_collector_combines_real_endpoint_shapes_without_inventing_asof():
    calls = []
    def fetch(path, *, api_key):
        calls.append(path)
        if path.startswith("/recruiting/"):
            return [{"year": 2023, "team": "Georgia", "points": 300.0, "rank": 1}]
        if path.startswith("/games?"):
            return [{"id": 1, "home_team": "Georgia", "away_team": "FCS Team"}]
        return [{"school": "Georgia"}]
    report = collect_snapshot([2023], api_key="fixture", fetch=fetch)
    assert len(calls) == 3
    assert report["fbs_teams_by_season"]["2023"] == ["Georgia"]
    assert report["classes"][0]["historical_asof_verified"] is False
    assert report["historical_asof_verified"] is False


def test_collector_rejects_partial_season():
    def fetch(path, *, api_key):
        return []
    with pytest.raises(ValueError, match="Missing CFBD data"):
        collect_snapshot([2023], api_key="fixture", fetch=fetch)


def test_collector_requires_unique_seasons_and_credentials():
    with pytest.raises(ValueError):
        collect_snapshot([2023, 2023], api_key="fixture")
    with pytest.raises(ValueError):
        collect_snapshot([2023], api_key="")


def test_collector_skips_unscored_classes_without_zero_imputation():
    def fetch(path, *, api_key):
        if path.startswith("/recruiting/"):
            return [{"year": 2023, "team": "Unranked", "points": None, "rank": None},
                    {"year": 2023, "team": "Georgia", "points": 300.0, "rank": 1}]
        if path.startswith("/games?"):
            return [{"id": 1, "home_team": "Georgia", "away_team": "FCS Team"}]
        return [{"school": "Georgia"}]
    report = collect_snapshot([2023], api_key="fixture", fetch=fetch)
    assert len(report["classes"]) == 1
    assert report["classes"][0]["team"] == "Georgia"
