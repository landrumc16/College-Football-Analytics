"""Normalize CFBD games into the model's canonical season snapshot.

No API credentials or network calls are required to run these functions.
"""
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IngestedGame:
    game_id: int
    season: int
    week: int
    home: str
    away: str
    completed: bool
    home_score: int | None
    away_score: int | None
    neutral_site: bool


def normalize_cfbd_games(records: list[dict[str, Any]], season: int) -> list[IngestedGame]:
    games = {}
    for row in records:
        if row.get("season") != season:
            continue
        game_id = row.get("id")
        if game_id is None:
            raise ValueError("CFBD game missing id")
        home = row.get("homeTeam", row.get("home_team"))
        away = row.get("awayTeam", row.get("away_team"))
        if not home or not away:
            # CFBD includes future games with TBD participants. They cannot be
            # modeled until both opponents are known.
            continue
        if home == away:
            raise ValueError(f"Invalid participants for game {game_id}")
        hs = row.get("homePoints", row.get("home_points"))
        ass = row.get("awayPoints", row.get("away_points"))
        # CFBD /games generally exposes scores, not a completed flag.
        # A 0-0 placeholder is not evidence that a game has finished.
        state = row.get("status")
        if row.get("completed") is not None:
            completed = row["completed"] is True
        elif state is not None:
            completed = str(state).lower() in ("final", "completed")
        else:
            completed = (isinstance(hs, int) and isinstance(ass, int)
                         and (hs != 0 or ass != 0))
        if completed and (not isinstance(hs, int) or not isinstance(ass, int)):
            raise ValueError(f"Completed game {game_id} missing integer scores")
        if completed and (hs < 0 or ass < 0):
            raise ValueError(f"Negative score for game {game_id}")
        game = IngestedGame(
            game_id=int(game_id), season=season, week=int(row.get("week") or 0),
            home=home, away=away, completed=completed,
            home_score=hs if completed else None,
            away_score=ass if completed else None,
            neutral_site=bool(row.get("neutralSite", row.get("neutral_site"))),
        )
        if game.game_id in games and games[game.game_id] != game:
            raise ValueError(f"Conflicting duplicate game id {game.game_id}")
        games[game.game_id] = game
    return sorted(games.values(), key=lambda g: (g.week, g.game_id))


def snapshot_summary(games: list[IngestedGame]) -> dict[str, int]:
    return {
        "scheduled": len(games),
        "completed": sum(g.completed for g in games),
        "pending": sum(not g.completed for g in games),
    }
