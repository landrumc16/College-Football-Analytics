import pytest
from cfb_analytics.v5_program_hype import hype_measurements

def observations():
    return [{"team":"Alpha","season":year,"poll":poll,
             "preseason_rank":25,"final_rank":10,
             "source":"https://example.org/polls","source_sha256":"a"*64}
            for year in range(2016,2026) for poll in ("AP","Coaches")]

def test_complete_reviewed_hype():
    result=hype_measurements(observations(),reviewed=True)
    assert result["Alpha"]["value"]==15
    assert result["Alpha"]["verified"] is True

def test_missing_poll_blocks_grade():
    assert hype_measurements(observations()[:-1])=={}

def test_unranked_proxy_is_explicit():
    rows=observations()
    rows[0]["preseason_rank"]=None
    rows[0]["final_rank"]=25
    result=hype_measurements(rows)
    assert result["Alpha"]["value"]==pytest.approx((19*15+1)/20)
    assert result["Alpha"]["verified"] is False

def test_duplicate_and_invalid_poll_rejected():
    with pytest.raises(ValueError,match="Duplicate"):
        hype_measurements(observations()+[observations()[0]])
    rows=observations()
    rows[0]["final_rank"]=27
    with pytest.raises(ValueError,match="Invalid poll"):
        hype_measurements(rows)
