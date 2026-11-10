"""Compute source-gated historical Hype Index measurements from AP/Coaches polls.

Rank 26 is an explicitly documented unranked proxy, not a fabricated
ranking. No historical grades are published until the input is reviewed.
"""
from collections import defaultdict

def hype_measurements(rows, *, seasons=range(2016,2026), reviewed=False):
    years=set(seasons)
    if not years:
        raise ValueError("No seasons")
    observations=defaultdict(dict)
    for row in rows:
        team,year,poll=row["team"],row["season"],row["poll"]
        if year not in years or poll not in ("AP","Coaches"):
            raise ValueError("Unexpected season or poll")
        key=(year,poll)
        if key in observations[team]:
            raise ValueError("Duplicate team-season-poll")
        source=row.get("source")
        sha=row.get("source_sha256")
        if not isinstance(source,str) or not source.startswith("https://") or not isinstance(sha,str) or len(sha)!=64:
            raise ValueError("Missing poll provenance")
        pre,final=row["preseason_rank"],row["final_rank"]
        if any(v is not None and (type(v) is not int or not 1<=v<=25) for v in (pre,final)):
            raise ValueError("Invalid poll rank")
        observations[team][key]=(26 if pre is None else pre)-(26 if final is None else final),source
    output={}
    for team,entries in observations.items():
        if set(entries)!={(year,poll) for year in years for poll in ("AP","Coaches")}:
            continue
        values=[value for value,_ in entries.values()]
        sources=sorted({source for _,source in entries.values()})
        output[team]={"value":sum(values)/len(values),"source":"; ".join(sources),
                      "verified":reviewed,
                      "method":"AP and Coaches average preseason-minus-final rank, unranked=26; all years required",
                      "seasons_observed":len(years)}
    return output
