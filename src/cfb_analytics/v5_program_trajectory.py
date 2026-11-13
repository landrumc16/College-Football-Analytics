"""Derive V5 3/5/10-year trajectory measurements from completed FBS records.

Accepts the existing schedule research artifact, not cross-season Elo. This
prepares measurements only; source review must occur before publication.
"""
from __future__ import annotations

from math import isfinite


def trajectory_measurements(records: dict, *, latest_completed_season: int, source: str,
                            source_reviewed: bool = False) -> dict:
    """Return per-team provenance-gated trajectory measurements.

    The score is the mean annual win-percentage slope across 3/5/10-year
    windows. Winning-percentage levels are retained separately for context;
    a consistently elite program is stable, not automatically rising.
    All windows require every year except the documented 2020 disruption;
    no missing records are silently treated as losses.
    """
    if not isinstance(source,str) or not source.startswith("https://"):
        raise ValueError("A public source URL is required")
    seasons=records.get("seasons")
    if not isinstance(seasons,list):
        raise ValueError("Missing season records")
    by_year={}
    for season in seasons:
        year=season["season"]
        if year in by_year:
            raise ValueError("Duplicate season")
        teams={}
        for row in season["teams"]:
            team=row["team"]
            if team in teams:
                raise ValueError("Duplicate team-season")
            wins,losses=row["fbs_wins"],row["fbs_losses"]
            if year == 2020 and wins == losses == 0:
                continue  # Some programs played no FBS opponents in 2020.
            if any(type(v) is not int or v<0 for v in (wins,losses)) or wins+losses==0:
                raise ValueError("Invalid FBS game record")
            teams[team]=(wins,losses)
        by_year[year]=teams
    expected={latest_completed_season-i for i in range(10)}-{2020}
    if not expected<=by_year.keys():
        raise ValueError("Missing required seasons")
    teams=set().union(*(set(by_year[y]) for y in expected))
    result={}
    for team in sorted(teams):
        windows={}
        slopes={}
        for span in (3,5,10):
            years=[latest_completed_season-i for i in range(span) if latest_completed_season-i!=2020]
            if not all(team in by_year.get(y,{}) for y in years):
                break
            wins=sum(by_year[y][team][0] for y in years)
            losses=sum(by_year[y][team][1] for y in years)
            windows[span]=wins/(wins+losses)
            mean_year=sum(years)/len(years)
            rates=[by_year[y][team][0]/sum(by_year[y][team]) for y in years]
            mean_rate=sum(rates)/len(rates)
            slopes[span]=sum((y-mean_year)*(rate-mean_rate) for y,rate in zip(years,rates))/sum((y-mean_year)**2 for y in years)
        if len(windows)==3:
            value=sum(slopes.values())/3
            if not isfinite(value):
                raise ValueError("Nonfinite trajectory")
            result[team]={"value":value,"source":source,"verified":source_reviewed,
                          "windows":{str(k):v for k,v in windows.items()},
                          "annual_slopes":{str(k):v for k,v in slopes.items()},
                          "direction":"rising" if value > .01 else "declining" if value < -.01 else "stable",
                          "method":"Mean 3/5/10-year annual FBS win-percentage slopes; 2020 excluded; stable within +/-1 percentage point/year"}
    return result
