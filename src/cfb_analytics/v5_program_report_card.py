"""Shared V5 Report Card grading; verified peer measurements only."""
from math import isfinite, fsum

CATEGORIES = ("hype", "trajectory", "strength")
BANDS = ((97,"A+"),(93,"A"),(90,"A-"),(87,"B+"),(83,"B"),(80,"B-"),(77,"C+"),(73,"C"),(70,"C-"),(67,"D+"),(63,"D"),(60,"D-"),(0,"F"))

def letter_grade(score):
    if isinstance(score,bool) or not isinstance(score,(int,float)) or not isfinite(score) or not 0 <= score <= 100:
        raise ValueError("Score must be finite and within 0..100")
    return next(label for threshold,label in BANDS if score >= threshold)

def build_report_cards(measurements, *, eligible_fbs, as_of, minimum_coverage=0.8):
    """Measurements: team -> category -> {value,source,verified}; larger is better.

    Midrank percentiles make category scores comparable; never extrapolate a
    national grade from an incomplete peer universe or unverified evidence.
    """
    if not isinstance(as_of,str) or not as_of.strip():
        raise ValueError("Missing as-of date")
    if isinstance(minimum_coverage,bool) or not isinstance(minimum_coverage,(int,float)) or not 0 < minimum_coverage <= 1:
        raise ValueError("Invalid coverage")
    if not isinstance(eligible_fbs,list) or not eligible_fbs or any(not isinstance(t,str) or not t.strip() for t in eligible_fbs) or len(set(eligible_fbs)) != len(eligible_fbs):
        raise ValueError("Invalid FBS universe")
    if set(measurements)-set(eligible_fbs):
        raise ValueError("Measurements outside FBS universe")
    peers=sorted(eligible_fbs)
    coverage={}
    scores={}
    for category in CATEGORIES:
        valid={}
        for team in peers:
            record=measurements.get(team,{}).get(category)
            if record is None:
                continue
            if not isinstance(record,dict) or not {"value","source","verified"} <= record.keys():
                raise ValueError("Malformed category measurement")
            if type(record["verified"]) is not bool:
                raise ValueError("Verification flag must be boolean")
            if not record["verified"]:
                continue
            value=record["value"]
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not isfinite(value):
                raise ValueError("Invalid category value")
            if not isinstance(record["source"],str) or not record["source"].strip():
                raise ValueError("Missing source")
            valid[team]=float(value)
        sufficient=len(valid)>=2 and len(valid)/len(peers)>=minimum_coverage
        coverage[category]={"verified":len(valid),"eligible":len(peers),"national_grades_available":sufficient}
        scores[category]={}
        if sufficient:
            values=list(valid.values())
            for team,value in valid.items():
                below=sum(v<value for v in values)
                tied=sum(v==value for v in values)
                scores[category][team]=100*(below+(tied-1)/2)/(len(values)-1)
    programs=[]
    for team in peers:
        categories={}
        for category in CATEGORIES:
            score=scores[category].get(team)
            categories[category]={"score":score,"grade":letter_grade(score) if score is not None else None}
        values=[categories[c]["score"] for c in CATEGORIES]
        overall=fsum(values)/3 if all(v is not None for v in values) else None
        programs.append({"team":team,"categories":categories,"overall_score":overall,"overall_grade":letter_grade(overall) if overall is not None else None})
    return {"schema_version":1,"as_of":as_of,"peer_universe":"eligible_FBS","eligible_fbs_count":len(peers),"minimum_coverage":minimum_coverage,"scoring":"verified peer midrank percentile; equal one-third weights","coverage":coverage,"programs":programs}
