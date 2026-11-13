import pytest
from cfb_analytics.v5_program_report_card import build_report_cards, letter_grade

def fixture(values):
    return {team:{cat:{"value":v,"source":"https://example.org/source","verified":True} for cat,v in categories.items()} for team,categories in values.items()}

def test_letter_boundaries():
    assert [letter_grade(v) for v in (0,60,63,70,80,90,93,97,100)] == ["F","D-","D","C-","B-","A-","A","A+","A+"]
    for value in (-1,101,float("nan"),float("inf"),True):
        with pytest.raises(ValueError):
            letter_grade(value)

def test_midrank_and_equal_weight():
    m=fixture({"A":{"hype":10,"trajectory":1,"strength":10},"B":{"hype":5,"trajectory":5,"strength":5},"C":{"hype":1,"trajectory":10,"strength":1}})
    result=build_report_cards(m,eligible_fbs=["A","B","C"],as_of="2026-11-10")
    a=result["programs"][0]
    assert a["categories"]["hype"]["score"]==100
    assert a["categories"]["trajectory"]["score"]==0
    assert a["overall_score"]==pytest.approx(200/3)
    assert a["overall_grade"]=="D"
    assert result["programs"][1]["overall_score"]==50

def test_ties():
    m=fixture({"A":{c:2 for c in ("hype","trajectory","strength")},"B":{c:2 for c in ("hype","trajectory","strength")},"C":{c:1 for c in ("hype","trajectory","strength")}})
    result=build_report_cards(m,eligible_fbs=["A","B","C"],as_of="2026-11-10")
    assert result["programs"][0]["overall_score"]==75
    assert result["programs"][1]["overall_score"]==75

def test_incomplete_national_coverage():
    m=fixture({"A":{c:1 for c in ("hype","trajectory","strength")},"B":{c:2 for c in ("hype","trajectory","strength")}})
    result=build_report_cards(m,eligible_fbs=["A","B","C"],as_of="2026-11-10")
    assert all(p["overall_grade"] is None for p in result["programs"])

def test_missing_category_not_reweighted():
    m=fixture({"A":{"hype":1,"trajectory":1,"strength":1},"B":{"hype":2,"trajectory":2,"strength":2},"C":{"hype":3,"trajectory":3}})
    result=build_report_cards(m,eligible_fbs=["A","B","C"],as_of="2026-11-10",minimum_coverage=.6)
    assert result["programs"][2]["overall_score"] is None
    assert result["programs"][2]["categories"]["hype"]["score"]==100

def test_unverified_not_published():
    m=fixture({"A":{c:1 for c in ("hype","trajectory","strength")},"B":{c:2 for c in ("hype","trajectory","strength")}})
    m["A"]["hype"]["verified"]=False
    result=build_report_cards(m,eligible_fbs=["A","B"],as_of="2026-11-10")
    assert all(p["overall_grade"] is None for p in result["programs"])
    m["A"]["hype"]["verified"]=True
    m["A"]["hype"]["value"]=float("nan")
    with pytest.raises(ValueError):
        build_report_cards(m,eligible_fbs=["A","B"],as_of="2026-11-10")


@pytest.mark.parametrize("flag", ["false", "true", 0, 1, None])
def test_nonboolean_verification_flags_cannot_publish_grades(flag):
    m=fixture({"A":{c:1 for c in ("hype","trajectory","strength")},
               "B":{c:2 for c in ("hype","trajectory","strength")}})
    m["A"]["hype"]["verified"]=flag
    with pytest.raises(ValueError,match="boolean"):
        build_report_cards(m,eligible_fbs=["A","B"],as_of="2026-11-13")
