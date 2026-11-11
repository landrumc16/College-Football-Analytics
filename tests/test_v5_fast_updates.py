import pytest
from cfb_analytics.v5_fast_updates import reconcile

A="https://scores.example.org/game/1"
B="https://conference.example.org/game/1"
DATE="2025-11-10T21:00:00-06:00"

def final(source=A, score=28):
    return dict(kind="game_final",game_id="123",home="Texas",away="Oklahoma",
                home_score=score,away_score=21,status="final",
                source=source,published_at=DATE)

def poll(source=A):
    return dict(kind="cfp_top25",season=2026,week=11,
                rankings=[dict(team=f"Team {i}",rank=i) for i in range(1,26)],
                source=source,published_at=DATE)

def test_one_source_only_provisional():
    assert reconcile([final()])["status"]=="provisional"

def test_two_independent_matching_scores_confirmed():
    result=reconcile([final(),final(B)])
    assert result["status"]=="confirmed"
    assert len(result["sources"])==2

def test_conflicting_scores_not_confirmed():
    assert reconcile([final(),final(B,score=27)])["status"]=="disputed"

def test_poll_confirmation_and_complete_25():
    assert reconcile([poll(),poll(B)])["status"]=="confirmed"
    broken=poll()
    broken["rankings"]=broken["rankings"][:-1]
    with pytest.raises(ValueError,match="complete"):
        reconcile([broken])

def test_duplicate_rank_rejected():
    broken=poll()
    broken["rankings"][1]["rank"]=1
    with pytest.raises(ValueError,match="Duplicate"):
        reconcile([broken])

def test_invalid_future_or_naive_timestamp_rejected():
    broken=final()
    broken["published_at"]="2026-11-10T21:00:00"
    with pytest.raises(ValueError,match="timezone"):
        reconcile([broken])

def test_mixed_kinds_rejected():
    with pytest.raises(ValueError,match="mixed"):
        reconcile([final(),poll()])

def test_confirmed_majority_with_disagreement_is_disputed():
    result=reconcile([final(),final(B),final("https://third.example.org/game/1",score=27)])
    assert result["status"]=="disputed"
    assert result["data"] is None

def test_two_urls_same_host_not_independent():
    second=final("https://scores.example.org/game/alternate")
    assert reconcile([final(),second])["status"]=="provisional"

def test_different_games_rejected():
    other=final(B)
    other["game_id"]="different"
    with pytest.raises(ValueError,match="different games"):
        reconcile([final(),other])

def test_different_poll_editions_rejected():
    other=poll(B)
    other["week"]=12
    with pytest.raises(ValueError,match="poll editions"):
        reconcile([poll(),other])


def test_same_provider_conflicting_urls_cannot_attest_to_confirmation():
    conflicting=final('https://scores.example.org/game/alternate',score=27)
    result=reconcile([final(),final(B),conflicting])
    assert result['status']=='disputed'
    assert result['data'] is None

def test_poll_rows_in_different_order_are_equivalent():
    second=poll(B)
    second['rankings'].reverse()
    assert reconcile([poll(),second])['status']=='confirmed'
