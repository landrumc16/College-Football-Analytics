import pytest
from cfb_analytics.v5_historical_results_comparison import compare_historical_results

A = "https://source-a.example/schedule"
B = "https://source-b.example/results"


def archive(rows):
    return {"seasons": [{"season": 2024, "teams": rows}]}


def record(team, wins=8, losses=4):
    return {"team": team, "fbs_wins": wins, "fbs_losses": losses}


def test_matching_records_only_are_accepted_and_disagreements_visible():
    left = archive([record("Alpha"), record("Beta", 4, 8), record("Gamma")])
    right = archive([record("Alpha"), record("Beta", 5, 7), record("Delta")])
    result = compare_historical_results(left, right, primary_source=A, independent_source=B)
    assert result["matching_count"] == 1
    assert result["accepted_matching_records"] == [{"season": 2024, "team": "Alpha", "fbs_wins": 8, "fbs_losses": 4}]
    assert result["exception_count"] == 3
    assert {x["reason"] for x in result["exceptions"]} == {"conflicting_record", "missing_source"}
    assert result["source_independence_attested"] is False


def test_no_second_source_never_promotes_records():
    with pytest.raises(ValueError, match="distinct"):
        compare_historical_results(archive([record("Alpha")]), archive([record("Alpha")]),
                                   primary_source=A, independent_source=A)


@pytest.mark.parametrize("rows", [
    [record("Alpha"), record("Alpha")],
    [record("Alpha", -1, 5)],
    [{"team": "Alpha", "fbs_wins": True, "fbs_losses": 5}],
])
def test_invalid_source_archive_fails_closed(rows):
    with pytest.raises(ValueError):
        compare_historical_results(archive(rows), archive([record("Alpha")]),
                                   primary_source=A, independent_source=B)


@pytest.mark.parametrize("mirror", [
    "https://api.collegefootballdata.com/games",
    "https://www.espn.com/college-football/",
    "https://github.com/sportsdataverse/cfbfastR-cfb-data",
])
def test_espn_redistributors_cannot_claim_independent_corroboration(mirror):
    rows = archive([record("Alpha")])
    with pytest.raises(ValueError, match="same upstream provider"):
        compare_historical_results(
            rows, rows,
            primary_source="https://github.com/sportsdataverse/sportsdataverse-data",
            independent_source=mirror)


def test_ncaa_and_espn_remain_comparable_but_not_automatically_attested():
    rows = archive([record("Alpha")])
    result = compare_historical_results(
        rows, rows,
        primary_source="https://github.com/sportsdataverse/sportsdataverse-data",
        independent_source="https://stats.ncaa.org/")
    assert result["matching_count"] == 1
    assert result["source_independence_attested"] is False
