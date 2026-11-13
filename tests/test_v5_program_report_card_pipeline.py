import pytest
from cfb_analytics.v5_program_report_card_pipeline import assemble_report_cards

SOURCE="https://example.org/verified"
def inputs():
    peers=["Alpha","Beta"]
    polls=[{"team":team,"season":year,"poll":poll,
            "preseason_rank":25 if team=="Alpha" else 10,
            "final_rank":10 if team=="Alpha" else 25,
            "source":SOURCE,"source_sha256":"a"*64}
           for team in peers for year in range(2016,2026)
           for poll in ("AP","Coaches")]
    records={"seasons":[{"season":year,"teams":[
        {"team":"Alpha","fbs_wins":8,"fbs_losses":2},
        {"team":"Beta","fbs_wins":2,"fbs_losses":8}]} for year in range(2016,2026)]}
    ratings=[{"team":"Alpha","rating":15},{"team":"Beta","rating":-5}]
    return dict(poll_rows=polls,season_records=records,current_rankings=ratings,
                eligible_fbs=peers,as_of="2026-11-10",latest_completed_season=2025,
                results_source=SOURCE,strength_source=SOURCE)

def test_all_three_categories_and_overall_use_same_pipeline():
    data=inputs()
    result=assemble_report_cards(**data,poll_reviewed=True,
                                 results_reviewed=True,strength_reviewed=True)
    assert result["programs"][0]["overall_score"]==100
    assert result["programs"][1]["overall_score"]==0
    assert result["programs"][0]["overall_grade"]=="A+"
    assert result["programs"][1]["overall_grade"]=="F"

def test_unreviewed_inputs_cannot_become_grades():
    result=assemble_report_cards(**inputs())
    assert all(p["overall_grade"] is None for p in result["programs"])
    assert not any(v["national_grades_available"] for v in result["coverage"].values())

def test_partial_source_review_only_enables_independent_categories():
    result=assemble_report_cards(**inputs(),strength_reviewed=True)
    assert result["coverage"]["strength"]["national_grades_available"]
    assert not result["coverage"]["hype"]["national_grades_available"]
    assert all(p["overall_grade"] is None for p in result["programs"])

def test_duplicate_v4_strength_is_rejected():
    data=inputs()
    data["current_rankings"].append(data["current_rankings"][0])
    with pytest.raises(ValueError,match="Duplicate"):
        assemble_report_cards(**data,strength_reviewed=True)


def test_unreviewed_malformed_history_does_not_block_reviewed_strength():
    data=inputs()
    data["poll_rows"]=[{"unreviewed":"incomplete"}]
    data["season_records"]={"unreviewed":"incomplete"}
    result=assemble_report_cards(**data,strength_reviewed=True)
    assert result["coverage"]["strength"]["national_grades_available"]
    assert not result["coverage"]["hype"]["national_grades_available"]
    assert not result["coverage"]["trajectory"]["national_grades_available"]
    assert all(row["overall_grade"] is None for row in result["programs"])


def test_unreviewed_malformed_strength_does_not_block_reviewed_history():
    data=inputs()
    data["current_rankings"]=[{"unreviewed":"incomplete"}]
    result=assemble_report_cards(**data,poll_reviewed=True,results_reviewed=True)
    assert result["coverage"]["hype"]["national_grades_available"]
    assert result["coverage"]["trajectory"]["national_grades_available"]
    assert not result["coverage"]["strength"]["national_grades_available"]
    assert all(row["overall_grade"] is None for row in result["programs"])
