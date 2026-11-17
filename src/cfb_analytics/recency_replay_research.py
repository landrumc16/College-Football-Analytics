"""Research-only paired chronological replay of incumbent and recency ratings.

Retrospective replay, NOT an archive of published pregame forecasts.
Requires season-specific as-of-eligible roster priors supplied by caller.
"""
from datetime import datetime, timedelta, timezone
from math import log
from .ratings import Game, Team, calculate_ratings
from .recency_rating_research import calculate_weighted_ratings
from .model import ModelSettings
from .predictions import predict


def _utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Missing kickoff timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Kickoff must include timezone")
    return dt.astimezone(timezone.utc)


def paired_replay(teams: list[Team], records: list[dict], *,
                  settings: ModelSettings = ModelSettings(),
                  result_delay_hours: float = 4.0) -> list[dict]:
    """Predict each completed fixture using only earlier eligible results.

    Conservative completion cutoff: kickoff + delay must precede target
    kickoff. Does not infer a final whistle or actual data publication time.
    Same-kickoff results are always excluded. Caller must verify historical
    roster/priors and result publication eligibility separately.
    """
    if result_delay_hours < 0:
        raise ValueError("result delay must be nonnegative")
    names = {t.name for t in teams}
    if len(names) != len(teams) or not names:
        raise ValueError("Invalid team roster")
    parsed = []
    ids = set()
    for r in records:
        game_id = r["game_id"]
        if game_id in ids:
            raise ValueError("Duplicate game ID")
        ids.add(game_id)
        kickoff = _utc(r["start_date"])
        home, away = r["home"], r["away"]
        if home == away:
            raise ValueError("Self matchup")
        if r.get("completed") is not True:
            continue
        hs, ass = r.get("home_score"), r.get("away_score")
        if (type(hs) is not int or type(ass) is not int or
                min(hs, ass) < 0 or hs == ass):
            raise ValueError("Invalid completed-game result")
        parsed.append((kickoff, str(game_id), r))
    parsed.sort(key=lambda item: (item[0], item[1]))
    output = []
    for kickoff, game_id, r in parsed:
        eligible = [(date, key, old) for date, key, old in parsed
                    if date < kickoff and
                    date + timedelta(hours=result_delay_hours) < kickoff]
        eligible.sort(key=lambda item: (item[0], item[1]))
        history = [Game(old["home"], old["away"],
                        old["home_score"], old["away_score"],
                        old.get("week", 0)) for _, _, old in eligible]
        baseline = calculate_ratings(teams, history, settings)
        challenger = calculate_weighted_ratings(teams, history, settings)
        home, away = r["home"], r["away"]
        def rating(result, name):
            if name not in names:
                return settings.fcs_opponent_rating
            item = result[name]
            return item.adaptive_rating if hasattr(item, "adaptive_rating") else item
        params = {"neutral": bool(r.get("neutral_site", False)),
                  "home_field_advantage": settings.home_field_advantage,
                  "model_scale": settings.win_probability_scale}
        b = predict(home, away, rating(baseline, home), rating(baseline, away), **params)
        c = predict(home, away, rating(challenger, home), rating(challenger, away), **params)
        output.append({
            "game_id": r["game_id"], "kickoff": kickoff.isoformat(),
            "week": r.get("week"), "home": home, "away": away,
            "home_won": int(r["home_score"] > r["away_score"]),
            "history_games": len(history),
            "incumbent_probability": b.model_home_probability,
            "challenger_probability": c.model_home_probability,
            "incumbent_margin": b.home_margin,
            "challenger_margin": c.home_margin,
            "actual_margin": r["home_score"] - r["away_score"],
        })
    return output


def paired_metrics(rows: list[dict]) -> dict:
    """Descriptive paired scoring; does not establish promotion eligibility."""
    if not rows:
        return {"games": 0, "incumbent": None, "challenger": None}
    def summarize(prefix):
        probabilities = [r[f"{prefix}_probability"] for r in rows]
        outcomes = [r["home_won"] for r in rows]
        eps = 1e-12
        return {
            "brier": sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / len(rows),
            "log_loss": -sum(y * log(max(eps, min(1-eps, p))) +
                             (1-y) * log(max(eps, min(1-eps, 1-p)))
                             for p, y in zip(probabilities, outcomes)) / len(rows),
            "winner_accuracy": sum((p >= .5) == bool(y)
                                   for p, y in zip(probabilities, outcomes)) / len(rows),
            "margin_mae": sum(abs(r[f"{prefix}_margin"] - r["actual_margin"])
                              for r in rows) / len(rows),
        }
    return {"games": len(rows), "incumbent": summarize("incumbent"),
            "challenger": summarize("challenger")}
