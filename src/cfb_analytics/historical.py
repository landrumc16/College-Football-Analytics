"""Versioned historical game records for V2 research, independent of V1 reports.

All timestamps must be timezone-aware; never infer kickoff or retrieval times.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

Division = Literal["FBS", "FCS", "OTHER", "UNKNOWN"]


def utc_instant(value: str | None) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None


@dataclass(frozen=True)
class HistoricalGame:
    season: int
    game_id: int
    home: str
    away: str
    home_division: Division
    away_division: Division
    kickoff: str
    source_retrieved_at: str
    source: str
    home_score: int | None = None
    away_score: int | None = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ValueError("Unsupported historical game schema")
        if self.season < 1869 or self.game_id <= 0:
            raise ValueError("Invalid season or game ID")
        if not self.home or not self.away or self.home == self.away:
            raise ValueError("Invalid participants")
        if self.home_division not in ("FBS", "FCS", "OTHER", "UNKNOWN"):
            raise ValueError("Invalid home division")
        if self.away_division not in ("FBS", "FCS", "OTHER", "UNKNOWN"):
            raise ValueError("Invalid away division")
        kickoff = utc_instant(self.kickoff)
        retrieved = utc_instant(self.source_retrieved_at)
        if kickoff is None or retrieved is None:
            raise ValueError("Kickoff and retrieval require aware timestamps")
        if not self.source.strip():
            raise ValueError("Missing source provenance")
        if (self.home_score is None) != (self.away_score is None):
            raise ValueError("Both scores must be present or absent")
        if self.home_score is not None:
            if (type(self.home_score) is not int or type(self.away_score) is not int
                    or min(self.home_score, self.away_score) < 0):
                raise ValueError("Scores must be nonnegative integers")

    @property
    def classification(self) -> str:
        divisions = (self.home_division, self.away_division)
        if divisions == ("FBS", "FBS"):
            return "fbs_vs_fbs"
        if set(divisions) == {"FBS", "FCS"}:
            return "fbs_vs_fcs"
        return "other_or_unverified"

    @property
    def eligible_fbs_accuracy(self) -> bool:
        return (self.classification == "fbs_vs_fbs"
                and self.home_score is not None
                and self.home_score != self.away_score)

    def verified_pregame(self, generated_at: str | None, input_retrieved_at: str | None = None) -> bool:
        """Validate forecast provenance independently of game-result retrieval."""
        generated = utc_instant(generated_at)
        kickoff = utc_instant(self.kickoff)
        inputs = utc_instant(input_retrieved_at)
        return (generated is not None and inputs is not None
                and inputs <= generated < kickoff)


def validate_unique_games(games: list[HistoricalGame]) -> None:
    seen: set[tuple[int, int]] = set()
    for game in games:
        key = (game.season, game.game_id)
        if key in seen:
            raise ValueError(f"Duplicate historical game: {key}")
        seen.add(key)
