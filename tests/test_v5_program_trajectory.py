import pytest
from cfb_analytics.v5_program_trajectory import trajectory_measurements

SOURCE="https://github.com/sportsdataverse/sportsdataverse-data"
def history(missing=None):
    return {"seasons":[{"season":y,"teams":[] if y==missing else [
        {"team":"Alpha","fbs_wins":8,"fbs_losses":2},
        {"team":"Beta","fbs_wins":2,"fbs_losses":8},
    ]} for y in range(2016,2026)]}

def test_complete_trajectory_without_historical_elo():
    rows=trajectory_measurements(history(),latest_completed_season=2025,source=SOURCE,source_reviewed=True)
    assert rows["Alpha"]["value"]==pytest.approx(0)
    assert rows["Beta"]["value"]==pytest.approx(0)
    assert rows["Alpha"]["verified"] is True
    assert rows["Alpha"]["windows"]=={"3":.8,"5":.8,"10":.8}

def test_review_is_not_automatic():
    rows=trajectory_measurements(history(),latest_completed_season=2025,source=SOURCE)
    assert rows["Alpha"]["verified"] is False

def test_2020_disruption_excluded():
    rows=history()
    for s in rows["seasons"]:
        if s["season"]==2020:
            s["teams"]=[]
    result=trajectory_measurements(rows,latest_completed_season=2025,source=SOURCE)
    assert result["Alpha"]["value"]==pytest.approx(0)

def test_missing_season_blocks_team_grade():
    assert "Alpha" not in trajectory_measurements(history(missing=2022),latest_completed_season=2025,source=SOURCE)

def test_duplicate_or_bad_records_rejected():
    rows=history()
    rows["seasons"].append(rows["seasons"][0])
    with pytest.raises(ValueError,match="Duplicate season"):
        trajectory_measurements(rows,latest_completed_season=2025,source=SOURCE)
    rows=history()
    rows["seasons"][0]["teams"][0]["fbs_wins"]=-1
    with pytest.raises(ValueError,match="Invalid FBS"):
        trajectory_measurements(rows,latest_completed_season=2025,source=SOURCE)


def test_elite_declining_and_weaker_rising_are_direction_not_strength():
    records=history()
    for season in records["seasons"]:
        offset=season["season"]-2016
        season["teams"][0].update(fbs_wins=19-offset, fbs_losses=1+offset)
        season["teams"][1].update(fbs_wins=1+offset, fbs_losses=19-offset)
    rows=trajectory_measurements(records,latest_completed_season=2025,source=SOURCE)
    assert rows["Alpha"]["windows"]["10"] > rows["Beta"]["windows"]["10"]
    assert rows["Alpha"]["value"]==pytest.approx(-.05)
    assert rows["Beta"]["value"]==pytest.approx(.05)
    assert rows["Alpha"]["direction"]=="declining"
    assert rows["Beta"]["direction"]=="rising"
