"""Descriptive pregame talent, transfer and returning-production matchup coverage.

Only independently dated observations can be compared; this is not a
forecast adjustment or a causal player-development/scouting grade.
"""
from .talent import features_as_of, ALLOWED, _timestamp


def talent_matchup_report(games, observations, *, cutoff_by_game):
    seen = set()
    output = []
    for game in games:
        game_id = game["game_id"]
        if game_id in seen:
            raise ValueError("Duplicate game id")
        seen.add(game_id)
        cutoff = cutoff_by_game.get(game_id)
        if _timestamp(cutoff) is None or _timestamp(game.get("kickoff")) is None or _timestamp(cutoff) >= _timestamp(game["kickoff"]):
            raise ValueError("Pregame cutoff required")
        known = features_as_of(observations, cutoff)
        home, away = game["home"], game["away"]
        if not home or not away or home == away:
            raise ValueError("Invalid teams")
        comparisons = []
        for feature in sorted(ALLOWED):
            h, a = known.get((home, feature)), known.get((away, feature))
            if h is None or a is None:
                continue
            comparisons.append({"feature": feature, "home_value": h["value"],
                                "away_value": a["value"],
                                "home_minus_away": h["value"]-a["value"],
                                "home_source": h["source"], "away_source": a["source"]})
        output.append({"game_id": game_id, "home": home, "away": away,
                       "comparisons": comparisons, "covered_features": len(comparisons),
                       "missing_features": len(ALLOWED)-len(comparisons)})
    return {"matchups": output, "scope": "source-backed pregame talent matchup research only"}
