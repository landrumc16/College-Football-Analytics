"""Adapt normalized CFBD game snapshots into V2 provenance-aware records.

Division membership must be supplied from season-specific authoritative rosters;
it is never inferred from a modern roster or from an opponent's name.
"""
from .historical import HistoricalGame, validate_unique_games
from .ingestion import IngestedGame


def historical_from_ingested(
    games: list[IngestedGame],
    *,
    retrieved_at: str,
    source: str,
    divisions_by_season: dict[int, dict[str, str]],
) -> list[HistoricalGame]:
    converted = []
    for game in games:
        if not game.start_date:
            raise ValueError(f"Missing kickoff for game {game.game_id}")
        divisions = divisions_by_season.get(game.season)
        if divisions is None:
            raise ValueError(f"Missing season-specific division roster: {game.season}")
        converted.append(HistoricalGame(
            season=game.season, game_id=game.game_id,
            home=game.home, away=game.away,
            home_division=divisions.get(game.home, "UNKNOWN"),
            away_division=divisions.get(game.away, "UNKNOWN"),
            kickoff=game.start_date,
            source_retrieved_at=retrieved_at,
            source=source,
            home_score=game.home_score if game.completed else None,
            away_score=game.away_score if game.completed else None,
        ))
    validate_unique_games(converted)
    return sorted(converted, key=lambda g: (g.season, g.game_id))
