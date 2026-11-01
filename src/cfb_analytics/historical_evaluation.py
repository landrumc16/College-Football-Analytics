"""Deterministic evaluation of verified historical FBS-vs-FBS forecasts.

This module is independent of the V1 published report and does not generate
predictions from completed-game information.
"""
from dataclasses import dataclass
from math import isfinite, log
from .historical import HistoricalGame, utc_instant, validate_unique_games


@dataclass(frozen=True)
class ArchivedForecast:
    season: int
    game_id: int
    home_win_probability: float
    generated_at: str
    input_retrieved_at: str | None = None

    def __post_init__(self):
        if not isfinite(self.home_win_probability) or not 0 <= self.home_win_probability <= 1:
            raise ValueError("Probability must be between zero and one")
        if utc_instant(self.generated_at) is None:
            raise ValueError("Forecast timestamp must include timezone")
        if self.input_retrieved_at is not None and utc_instant(self.input_retrieved_at) is None:
            raise ValueError("Forecast input timestamp must include timezone")


def evaluate_forecasts(games: list[HistoricalGame],
                       forecasts: list[ArchivedForecast]) -> dict:
    """Score only eligible pre-kickoff FBS games, never retrofitted forecasts."""
    validate_unique_games(games)
    by_game = {(g.season, g.game_id): g for g in games}
    if len({(f.season, f.game_id) for f in forecasts}) != len(forecasts):
        raise ValueError("Duplicate forecasts")
    scored = []
    exclusions = {"unknown_game": 0, "ineligible_game": 0, "not_pregame": 0}
    for forecast in sorted(forecasts, key=lambda f: (f.season, f.game_id)):
        game = by_game.get((forecast.season, forecast.game_id))
        if game is None:
            exclusions["unknown_game"] += 1
            continue
        if not game.eligible_fbs_accuracy:
            exclusions["ineligible_game"] += 1
            continue
        if not game.verified_pregame(forecast.generated_at, forecast.input_retrieved_at):
            exclusions["not_pregame"] += 1
            continue
        actual = int(game.home_score > game.away_score)
        scored.append((forecast.home_win_probability, actual, forecast.season))
    result = {"games": len(scored), "excluded": exclusions,
              "evaluation_scope": "verified pregame forecasts with input-snapshot provenance; FBS-vs-FBS"}
    if not scored:
        return {**result, "metrics": None, "by_season": {}}

    def metrics(rows):
        n = len(rows)
        return {
            "games": n,
            "winner_accuracy": sum((p >= 0.5) == bool(y) for p, y, _ in rows) / n,
            "brier_score": sum((p-y)**2 for p, y, _ in rows) / n,
            "log_loss": -sum(y*log(max(1e-15, p)) +
                             (1-y)*log(max(1e-15, 1-p))
                             for p, y, _ in rows) / n,
        }
    seasons = sorted({season for _, _, season in scored})
    return {**result, "metrics": metrics(scored),
            "by_season": {str(season): metrics([row for row in scored
                                               if row[2] == season])
                          for season in seasons}}
