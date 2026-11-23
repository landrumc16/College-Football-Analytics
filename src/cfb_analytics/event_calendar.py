"""When football information is expected to change (pure functions; no I/O).

The calendar tells the watcher *when to look*; it never decides that something happened. A game is final only when
the source says so, and a poll is published only when a complete poll for the expected week appears. Events whose
expected window has passed stay "overdue" and keep being monitored until resolved.

Windows (all derived from published kickoff times and the official release calendar):
- Games: a kickoff-based completion window from kickoff + 2h15 (early finishes) to kickoff + 4h45 (overtime,
  replay-heavy games). Unresolved games after that stay overdue for 36 hours (delays, suspensions), then drop to the
  daily baseline refresh, which still reconciles them.
- AP and Coaches polls: Sunday 11:00-16:00 US Central for the week just completed; if not published by then they stay
  overdue through Monday, then fall back to the existing daily poll schedule.
- CFP rankings: the published 2026 release dates (`poll_refresh.CFP_DATES`), 17:00-21:00 Central (selection Sunday
  10:00-14:00). CFP detection is reported for manual verification; it is never auto-published (see poll_refresh).
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .poll_refresh import CFP_DATES

CENTRAL = ZoneInfo("America/Chicago")
EARLY_FINISH = timedelta(hours=2, minutes=15)
LATE_FINISH = timedelta(hours=4, minutes=45)
OVERDUE_LIMIT = timedelta(hours=36)
ACTIVE_INTERVAL = 300      # seconds between source checks while an event is due (CFBD call budget; configurable)
WATCH_INTERVAL = 900       # seconds between checks of overdue (delayed, suspended) games


def parse_time(value):
    if not value:
        return None
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


@dataclass
class Plan:
    now: datetime
    intensity: str                       # "active" | "watch" | "idle"
    interval: int | None                 # seconds until the next check, None when idle
    games_due: list = field(default_factory=list)      # in their completion window
    games_overdue: list = field(default_factory=list)  # past the window, still not final
    games_in_progress: list = field(default_factory=list)
    polls_due: list = field(default_factory=list)      # "ap_top25" / "coaches_top25" for the expected week
    cfp_due: bool = False
    next_event_at: datetime | None = None

    @property
    def monitors_games(self):
        return bool(self.games_due or self.games_overdue)

    def summary(self):
        return {"intensity": self.intensity, "interval_seconds": self.interval, "games_due": len(self.games_due),
                "games_overdue": len(self.games_overdue), "games_in_progress": len(self.games_in_progress),
                "polls_due": self.polls_due, "cfp_due": self.cfp_due,
                "next_event_at": self.next_event_at.isoformat() if self.next_event_at else None}


def game_status(game, now):
    """Window status of one non-final game: upcoming, in_progress, due, overdue or expired."""
    kickoff = parse_time(game.get("start_date"))
    if game.get("completed") or kickoff is None:
        return "final" if game.get("completed") else "unscheduled"
    if now < kickoff:
        return "upcoming"
    if now < kickoff + EARLY_FINISH:
        return "in_progress"
    if now <= kickoff + LATE_FINISH:
        return "due"
    if now <= kickoff + LATE_FINISH + OVERDUE_LIMIT:
        return "overdue"
    return "expired"


def expected_poll_week(snapshot, now):
    """Poll week due next. Polls are numbered for the coming week: the poll released after week N's games is week
    N + 1 (the AP poll published 2026-11-16, after week 11, is week 12)."""
    weeks = [g["week"] for g in snapshot["games"] if (k := parse_time(g.get("start_date"))) and k <= now and isinstance(g.get("week"), int)]
    return max(weeks) + 1 if weeks else None


def poll_window(now):
    """('due' | 'overdue' | None) for the Sunday AP/Coaches release, by Central time."""
    local = now.astimezone(CENTRAL)
    hour = local.hour + local.minute / 60
    if not 8 <= local.month <= 12 and local.month != 1:
        return None
    if local.weekday() == 6 and 11 <= hour < 16:
        return "due"
    if (local.weekday() == 6 and hour >= 16) or local.weekday() == 0:
        return "overdue"
    return None


def cfp_window(now, year=2026):
    local = now.astimezone(CENTRAL)
    if local.year != year or (local.month, local.day) not in CFP_DATES:
        return False
    hour = local.hour + local.minute / 60
    return 10 <= hour < 14 if local.weekday() == 6 else 17 <= hour < 21


def plan(snapshot, polls, now, *, active_interval=ACTIVE_INTERVAL, watch_interval=WATCH_INTERVAL):
    """Monitoring plan for `now` from the current game snapshot and published poll snapshot."""
    p = Plan(now=now, intensity="idle", interval=None)
    upcoming = []
    for g in snapshot["games"]:
        s = game_status(g, now)
        if s == "due":
            p.games_due.append(g)
        elif s == "overdue":
            p.games_overdue.append(g)
        elif s == "in_progress":
            p.games_in_progress.append(g)               # cannot be final yet: no source check until its window opens
            upcoming.append(parse_time(g["start_date"]) + EARLY_FINISH)
        elif s == "upcoming":
            upcoming.append(parse_time(g["start_date"]) + EARLY_FINISH)
    week = expected_poll_week(snapshot, now)
    window = poll_window(now)
    if window and week is not None:
        published = (polls or {}).get("poll_weeks", {})
        p.polls_due = [k for k in ("ap_top25", "coaches_top25") if (published.get(k) or 0) < week]
    p.cfp_due = cfp_window(now)
    if p.games_due or p.polls_due or p.cfp_due:
        p.intensity, p.interval = "active", active_interval
    elif p.games_overdue:
        p.intensity, p.interval = "watch", watch_interval
    starts = sorted(t for t in upcoming if t > now)
    p.next_event_at = starts[0] if starts else None
    return p
