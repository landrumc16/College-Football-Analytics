"""Validate historical source extracts before any V4 modeling.

These checks establish source integrity, not pregame feature availability.
"""
from datetime import datetime
from math import isfinite


def validate_season_games(rows: list[dict], season: int) -> dict:
    if not rows:
        raise ValueError("Empty historical season")
    seen = set()
    fbs_fbs = fbs_fcs = 0
    for game in rows:
        if game.get("season") != season:
            raise ValueError("Mixed seasons")
        game_id = str(game.get("game_id") or "")
        if not game_id or game_id in seen:
            raise ValueError("Missing or duplicate game ID")
        seen.add(game_id)
        if not isinstance(game.get("week"), int) or game["week"] < 1:
            raise ValueError("Missing or invalid game week")
        kickoff = game.get("kickoff")
        try:
            dt = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
            if dt.tzinfo is None or dt.utcoffset() is None:
                raise ValueError("Timezone missing")
        except (AttributeError, TypeError, ValueError) as exc:
            raise ValueError("Invalid timezone-aware kickoff") from exc
        if not game.get("home") or not game.get("away") or game["home"] == game["away"]:
            raise ValueError("Invalid team matchup")
        for side in ("home", "away"):
            score = game.get(f"{side}_score")
            if isinstance(score, bool) or not isinstance(score, int) or score < 0:
                raise ValueError("Invalid final score")
        if game.get("fbs_participant") is not True:
            raise ValueError("Non-FBS-participant game in FBS extract")
        divisions = {game.get("home_division"), game.get("away_division")}
        if game.get("fbs_game") is True:
            if divisions != {"FBS"}:
                raise ValueError("Contradictory FBS-vs-FBS classification")
            fbs_fbs += 1
        else:
            if "FBS" not in divisions:
                raise ValueError("FBS participant has no verified FBS side")
            if "FCS" in divisions:
                fbs_fcs += 1
    return {"season": season, "games": len(rows),
            "fbs_fbs": fbs_fbs, "fbs_fcs": fbs_fcs,
            "other_fbs_opponent": len(rows) - fbs_fbs - fbs_fcs}
