"""Join existing historical and current V4 data into one verified Report Card.

This is an assembly step, not a new prediction or strength model. The
caller supplies the incumbent V4 team ratings and an independently verified
eligible-FBS roster. Research-only records remain unverified.
"""
from .v5_program_hype import hype_measurements
from .v5_program_trajectory import trajectory_measurements
from .v5_program_report_card import build_report_cards


def assemble_report_cards(*, poll_rows, season_records, current_rankings,
                          eligible_fbs, as_of, latest_completed_season,
                          poll_reviewed=False, results_reviewed=False,
                          strength_reviewed=False, strength_source="",
                          results_source="", minimum_coverage=0.8):
    if not isinstance(eligible_fbs, list) or not eligible_fbs:
        raise ValueError("Verified eligible FBS roster required")
    if not isinstance(current_rankings,list):
        raise ValueError("Current V4 rankings must be a list")
    hype=hype_measurements(poll_rows, reviewed=poll_reviewed)
    trajectory=trajectory_measurements(
        season_records, latest_completed_season=latest_completed_season,
        source=results_source, source_reviewed=results_reviewed)
    strength={}
    for row in current_rankings:
        team=row["team"]
        if team in strength:
            raise ValueError("Duplicate incumbent strength")
        rating=row.get("rating")
        if type(rating) not in (int,float):
            raise ValueError("Invalid incumbent rating")
        strength[team]={"value":rating,"source":strength_source,
                        "verified":strength_reviewed}
    measurements={}
    for team in eligible_fbs:
        measurements[team]={}
        for category,values in (("hype",hype),("trajectory",trajectory),("strength",strength)):
            if team in values:
                measurements[team][category]=values[team]
    result=build_report_cards(measurements,eligible_fbs=eligible_fbs,
                              as_of=as_of,minimum_coverage=minimum_coverage)
    result["source_review"]={
        "polls":poll_reviewed,"historical_results":results_reviewed,
        "incumbent_strength":strength_reviewed}
    return result
