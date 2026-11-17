"""Research-only verified lineup-change advisory, independent of forecasts.

No player impact guesses or score adjustments. Source records must be supplied
by a separately verified workflow; this module does not discover injuries.
"""
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class LineupChange:
    team: str
    position: str
    change: str
    effective_at: str
    source_url: str
    verified_at: str
    games_with_new_lineup: int
    current_lineup_confirmed: bool = True


@dataclass(frozen=True)
class LineupAdvisory:
    team: str
    headline: str
    message: str
    games_observed: int
    provisional_window: int
    source_url: str
    verified_at: str


def lineup_advisory(change: LineupChange | None, *, as_of: str,
                    provisional_window: int = 3) -> LineupAdvisory | None:
    """Return advisory only for valid, verified, currently relevant changes.

    The three-game window is provisional and is not a measure of accuracy.
    A caller must establish actual starter participation before incrementing
    games_with_new_lineup; a bye does not count.
    """
    if change is None:
        return None
    if provisional_window < 1:
        raise ValueError("provisional_window must be positive")

    def parse(value: str) -> datetime:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("timestamps must include timezone")
        return result.astimezone(timezone.utc)

    cutoff = parse(as_of)
    effective, verified = parse(change.effective_at), parse(change.verified_at)
    if effective > cutoff or verified > cutoff:
        return None
    if (not change.team.strip() or not change.position.strip()
            or change.change not in {"replacement", "injury", "return"}
            or not change.source_url.startswith(("https://", "http://"))
            or change.games_with_new_lineup < 0
            or not change.current_lineup_confirmed
            or change.games_with_new_lineup >= provisional_window):
        return None
    return LineupAdvisory(
        team=change.team,
        headline="Lineup change: forecast uncertainty elevated",
        message=(f"Verified {change.position} lineup change. The forecast may be "
                 "less reliable until more games show how the current lineup performs."),
        games_observed=change.games_with_new_lineup,
        provisional_window=provisional_window,
        source_url=change.source_url,
        verified_at=change.verified_at,
    )
