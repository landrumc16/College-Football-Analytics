"""Matchup diagnostics using only source-backed, pre-kickoff scheme features.

Differences describe measured team tendencies; they are not validated betting
edges or an automatic adjustment to the production win probability.
"""
from .coaching import scheme_as_of, TENDENCIES
from .talent import _timestamp


def matchup_scheme_diagnostics(games, schemes, *, cutoff_by_game):
    seen = set()
    output = []
    for game in games:
        game_id = game["game_id"]
        if game_id in seen:
            raise ValueError("Duplicate matchup game id")
        seen.add(game_id)
        cutoff = cutoff_by_game.get(game_id)
        if _timestamp(cutoff) is None or _timestamp(game.get("kickoff")) is None or _timestamp(cutoff) >= _timestamp(game["kickoff"]):
            raise ValueError("Explicit pre-kickoff cutoff required")
        home, away = game["home"], game["away"]
        if not home or not away or home == away:
            raise ValueError("Invalid matchup teams")
        known = scheme_as_of(schemes, cutoff)
        comparisons = []
        for feature in sorted(TENDENCIES):
            h, a = known.get((home, feature)), known.get((away, feature))
            if h is None or a is None:
                continue
            comparisons.append({"feature": feature, "home_value": h["value"],
                                "away_value": a["value"],
                                "home_minus_away": h["value"]-a["value"],
                                "home_source": h["source"], "away_source": a["source"]})
        output.append({"game_id": game_id, "home": home, "away": away,
                       "cutoff": cutoff, "comparisons": comparisons,
                       "covered_metrics": len(comparisons),
                       "missing_metrics": len(TENDENCIES)-len(comparisons)})
    return {"matchups": output, "scope": "pre-kickoff descriptive scheme comparisons; no validated forecast adjustment"}
