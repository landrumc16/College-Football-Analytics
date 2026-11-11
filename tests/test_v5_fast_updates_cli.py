from cfb_analytics.v5_fast_updates_cli import publish
from test_v5_fast_updates import final, poll, A, B
import pytest


def test_provisional_never_replaces_confirmed_game():
    previous={"confirmed": final(A, 28)}
    out=publish([final(B, 27)],previous)
    assert out["status"]=="provisional"
    assert out["confirmed"]["home_score"]==28
    assert not out["model_ingestion_allowed"]


def test_dispute_never_replaces_confirmed_game():
    previous={"confirmed": final(A, 28)}
    out=publish([final(A, 27),final(B, 26)],previous)
    assert out["status"]=="disputed"
    assert out["confirmed"]["home_score"]==28
    assert out["provisional"] is None
    assert not out["model_ingestion_allowed"]


def test_matching_independent_reports_promote():
    out=publish([final(),final(B)])
    assert out["status"]=="confirmed"
    assert out["confirmed"]["home_score"]==28
    assert out["model_ingestion_allowed"]


def test_old_poll_cannot_replace_new_poll():
    newer=poll()
    newer["week"]=12
    with pytest.raises(ValueError,match="older"):
        publish([poll(),poll(B)],{"confirmed":newer})


def test_conflicting_same_week_confirmed_poll_is_rejected():
    old=poll()
    old["rankings"][0]["team"]="Different"
    with pytest.raises(ValueError,match="Conflicting confirmed"):
        publish([poll(),poll(B)],{"confirmed":old})


def test_unrelated_confirmed_game_rejected():
    old=final()
    old["game_id"]="another"
    with pytest.raises(ValueError,match="identifier"):
        publish([final(),final(B)],{"confirmed":old})


def test_same_confirmed_poll_different_row_order_is_idempotent():
    previous=poll()
    second=poll(B)
    second["rankings"].reverse()
    result=publish([poll(),second],{"confirmed":previous})
    assert result["status"]=="confirmed"
    assert result["model_ingestion_allowed"]


def test_disputed_majority_does_not_replace_prior_confirmed():
    previous={"confirmed":final(A,28)}
    out=publish([final(A,29),final(B,29),final("https://third.example.org/game/1",30)],previous)
    assert out["status"]=="disputed"
    assert out["confirmed"]["home_score"]==28
    assert out["model_ingestion_allowed"] is False
