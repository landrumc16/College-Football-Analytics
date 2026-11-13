"""Compute source-gated historical Hype Index measurements from AP/Coaches polls.

Rank 26 is an explicitly documented unranked proxy, not a fabricated
ranking. No historical grades are published until the input is reviewed.
"""
from collections import defaultdict
import re

def hype_measurements(rows, *, seasons=range(2016,2026), reviewed=False):
    years=set(seasons)
    if not years:
        raise ValueError("No seasons")
    observations=defaultdict(dict)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid poll observation")
        team,year,poll=row.get("team"),row.get("season"),row.get("poll")
        if not isinstance(team,str) or not team.strip() or type(year) is not int:
            raise ValueError("Invalid team or season identity")
        if year not in years or poll not in ("AP","Coaches"):
            raise ValueError("Unexpected season or poll")
        key=(year,poll)
        if key in observations[team]:
            raise ValueError("Duplicate team-season-poll")
        source=row.get("source")
        sha=row.get("source_sha256")
        if not isinstance(source,str) or not source.startswith("https://") or not isinstance(sha,str) or re.fullmatch(r"[0-9a-fA-F]{64}",sha) is None:
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
