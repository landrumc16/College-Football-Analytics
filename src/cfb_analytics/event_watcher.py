"""Event-driven game-day watcher: look when the calendar says, act when the source changes, verify on the live site.

  python -m cfb_analytics.event_watcher            # used by .github/workflows/event-watcher.yml
  python -m cfb_analytics.event_watcher --dry-run  # one real check of every provider; dispatches nothing

It reuses the existing pipeline instead of replacing it:
- Detection: CFBD /games (the same source the refresh uses, so the detecting source is also the authoritative one)
  and CFBD /rankings (the same source poll_refresh uses).
- Action: dispatches the existing "Refresh college football data" / "Refresh official college football polls"
  workflows (workflow_dispatch is allowed from GITHUB_TOKEN, unlike pushes); those rebuild, validate and trigger the
  dashboard deployment exactly as today.
- Verification: reads the live site's season-report.json / poll-snapshot.json until the change is visible and records
  detection-to-publication latency. A dispatch whose change does not appear is retried once and then alerted.

Safety: a source failure backs off only that source; stale responses (a final game reported as not final, missing
scores, a smaller poll week) are ignored and logged; repeated detections are deduplicated by game id and score; the
CFBD call budget is capped per run.

Release detection without CFBD: during and after each scheduled CFP announcement the watcher reads the dated official
page itself every 30 seconds (no CFBD call). Only a complete parse (ranks 1-25, known programs, the release date stated)
spends a CFBD call to confirm every position; the poll workflow then re-checks both and publishes. Confirmation and
publication of releases draw on a priority allowance that may spend down to RELEASE_FLOOR, so a release day never has
a zero budget while the discretionary game budget is exhausted.

Reliable execution: each run queues its successor when it starts (see chain_successor) and stays alive until its
deadline while the season still has games to watch (event_calendar.horizon_active). The workflow's concurrency group allows one running and one queued run,
so chained, scheduled and keeper-started runs never overlap; a start-rate cap stops a crash loop. If the chain stops,
watch_keeper restarts it from any other workflow run, the hourly schedule remains a backup, and freshness_monitor
raises an alert.
"""
import argparse
import json
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from datetime import date

from . import cfp_publish
from . import event_calendar as cal
from .ingestion import normalize_cfbd_games
from .poll_refresh import choose_polls

SITE = "https://landrumc16.github.io/College-Football-Analytics/"
REPO = "landrumc16/College-Football-Analytics"
VERIFY_TIMEOUT = timedelta(minutes=20)   # refresh ~1 min + build/deploy ~5 min measured; generous before a retry
RECONCILE_WINDOW = timedelta(hours=2)    # keep checking recently finalized games for authoritative corrections
RECONCILE_INTERVAL = 1800                # ... every 30 minutes (any other check also reconciles: one call returns all games)
# CFBD quota (free tier: 1,000 calls a month, verified with GET /info). The watcher spends only what is left after
# reserving the calls the scheduled workflows need until the monthly reset.
RESERVE_PER_DAY = 6      # daily baseline refresh (games, lines x2, postseason) + poll and statistics refreshes
REFRESH_COST = 4         # CFBD calls one dispatched data refresh spends
POLL_REFRESH_COST = 2    # poll refresh + CFP confirmation
MIN_INTERVAL = 120       # never check more often than every 2 minutes
# Releases (AP/Coaches polls, CFP rankings) have priority: their checks may spend down to this floor, which keeps one
# daily baseline refresh plus margin. The discretionary game budget stops at the full reserve above.
RELEASE_FLOOR = 8
CFP_PAGE_INTERVAL = 30   # seconds between official CFP page reads while a release is due (free: no CFBD call)
CFP_WATCH_LIMIT = timedelta(hours=24)   # keep reading the official page this long after the announcement time
CFP_CONFIRM_MAX = 4      # CFBD confirmation attempts per CFP release (backing off 2, 4, 8 minutes)
CFP_RELEASE_COST = CFP_CONFIRM_MAX + 2 * POLL_REFRESH_COST     # confirmations + publication + one re-dispatch
POLL_CHECKS = 6          # priority CFBD checks for one AP/Coaches release when the discretionary budget is empty
POLL_RELEASE_COST = POLL_CHECKS + 2 * POLL_REFRESH_COST
VERIFY_POLL = 15         # seconds between live-site reads while a publication is awaited (free)
MONITOR_INTERVAL = 600   # seconds between freshness monitor passes (GitHub API and live site only)
MAX_STARTS_PER_HOUR = 4  # watcher starts per hour beyond which the chain stops itself and alerts (crash loop)
WAITING_RUN = {"queued", "pending", "waiting", "requested"}
ACTIVE_RUN = WAITING_RUN | {"in_progress"}


def utcnow():
    return datetime.now(timezone.utc)


def _get_json(url, headers=None, timeout=30):
    with urlopen(Request(url, headers={"Accept": "application/json", **(headers or {})}), timeout=timeout) as r:
        return json.load(r)


class Providers:
    """Real providers. Every method raises on failure; the watcher isolates and backs off per source."""

    def __init__(self, cfbd_key, github_token, repo=REPO, site=SITE):
        self.cfbd_key, self.github_token, self.repo, self.site = cfbd_key, github_token, repo, site
        self.cfbd_calls = 0

    def games(self, season):
        self.cfbd_calls += 1
        return _get_json(f"https://api.collegefootballdata.com/games?year={season}&seasonType=regular",
                         {"Authorization": f"Bearer {self.cfbd_key}"}, timeout=45)

    def rankings(self, season):
        self.cfbd_calls += 1
        return _get_json(f"https://api.collegefootballdata.com/rankings?year={season}&seasonType=regular",
                         {"Authorization": f"Bearer {self.cfbd_key}"}, timeout=45)

    def dispatch(self, workflow, inputs=None):
        body = json.dumps({"ref": "main", "inputs": inputs or {}}).encode()
        req = Request(f"https://api.github.com/repos/{self.repo}/actions/workflows/{workflow}/dispatches", data=body, method="POST",
                      headers={"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28"})
        with urlopen(req, timeout=30) as r:
            if r.status != 204:
                raise RuntimeError(f"dispatch {workflow} returned {r.status}")

    def info(self):
        """CFBD account tier and remaining monthly calls (GET /info)."""
        return _get_json("https://api.collegefootballdata.com/info", {"Authorization": f"Bearer {self.cfbd_key}"})

    def postseason(self, season):
        self.cfbd_calls += 1
        return _get_json(f"https://api.collegefootballdata.com/games?year={season}&seasonType=postseason",
                         {"Authorization": f"Bearer {self.cfbd_key}"}, timeout=45)

    def official_page(self, url):
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; cfb-analytics-verifier)"}), timeout=30) as r:
            return r.read().decode("utf-8", "replace")

    def workflows(self):
        return _get_json(f"https://api.github.com/repos/{self.repo}/actions/workflows",
                         {"Authorization": f"Bearer {self.github_token}"})

    def github(self, path, method="GET", body=None):
        """GitHub REST call for the repository (path relative to /repos/{repo}/); returns parsed JSON or None."""
        req = Request(f"https://api.github.com/repos/{self.repo}/{path}", method=method,
                      data=json.dumps(body).encode() if body is not None else None,
                      headers={"Authorization": f"Bearer {self.github_token}", "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
        with urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else None

    def workflow_runs(self, workflow, per_page=30):
        return self.github(f"actions/workflows/{workflow}/runs?per_page={per_page}").get("workflow_runs", [])

    def watcher_runs(self):
        return self.workflow_runs("event-watcher.yml", 20)

    def cfp_page(self, url):
        """The official release page, or None while it does not exist yet (404). No CFBD call."""
        return cfp_publish.fetch_page(url)

    def live_report(self):
        return _get_json(self.site + f"season-report.json?t={int(time.time())}")

    def live_postseason(self):
        try:
            return _get_json(self.site + f"postseason-2026.json?t={int(time.time())}")
        except Exception:
            return {"games": []}

    def live_polls(self):
        return _get_json(self.site + f"poll-snapshot.json?t={int(time.time())}")


def normalise(raw, season=2026):
    """CFBD /games rows -> {game_id: {completed, home_score, away_score, start_date}} via the pipeline's own ingestion."""
    out = {}
    for g in normalize_cfbd_games(raw or [], season):
        out[int(g.game_id)] = {"completed": g.completed, "home_score": g.home_score, "away_score": g.away_score, "start_date": g.start_date}
    return out


@dataclass
class Event:
    kind: str                     # final | correction | reschedule | poll | cfp
    key: str                      # dedupe key
    detail: dict
    detected_at: datetime
    source: str
    dispatched_at: datetime | None = None
    published_at: datetime | None = None
    attempts: int = 0
    status: str = "detected"      # detected | dispatched | published | alerted | recorded
    available_after: datetime | None = None   # last check that did NOT see it: the change appeared after this moment
    confirmed_at: datetime | None = None      # independent confirmation (CFP: CFBD agreed with the official page)
    priority: bool = False                    # paid from the release allowance

    def record(self):
        lat = lambda a, b: round((b - a).total_seconds()) if a and b else None
        verified = self.confirmed_at or self.detected_at
        return {"kind": self.kind, "key": self.key, "detail": self.detail, "source": self.source, "status": self.status,
                "available_after": self.available_after and self.available_after.isoformat(),
                "detected_at": self.detected_at.isoformat(), "confirmed_at": self.confirmed_at and self.confirmed_at.isoformat(),
                "dispatched_at": self.dispatched_at and self.dispatched_at.isoformat(),
                "published_at": self.published_at and self.published_at.isoformat(), "attempts": self.attempts,
                # Stage latencies. Detection is bounded by the previous check that did not see the change.
                "detection_seconds_at_most": lat(self.available_after, self.detected_at),
                "verification_seconds": lat(self.detected_at, self.confirmed_at) if self.confirmed_at else 0,
                "publication_seconds": lat(verified, self.published_at),
                "detection_to_publication_seconds": lat(self.detected_at, self.published_at),
                "total_seconds_at_most": lat(self.available_after or self.detected_at, self.published_at)}


@dataclass
class SourceHealth:
    failures: int = 0
    next_allowed: datetime | None = None
    last_error: str | None = None

    def ok(self, now):
        return self.next_allowed is None or now >= self.next_allowed

    def fail(self, now, error, base):
        self.failures += 1
        self.last_error = str(error)[:200]
        self.next_allowed = now + timedelta(seconds=min(base * 2 ** (self.failures - 1), 1800))

    def recover(self):
        self.failures, self.next_allowed, self.last_error = 0, None, None


def releases_due_today(snapshot, polls, now):
    """AP/Coaches or CFP releases expected later today (Central) and not yet published."""
    local = now.astimezone(cal.CENTRAL)
    week = cal.expected_poll_week(snapshot, now)
    published = (polls or {}).get("poll_weeks", {})
    poll = local.weekday() in (6, 0) and week is not None and any((published.get(k) or 0) < week for k in ("ap_top25", "coaches_top25"))
    cfp = local.year == 2026 and (local.month, local.day) in cal.CFP_DATES
    return {"polls": bool(poll), "cfp": bool(cfp)}


def quota_plan(info, snapshot, now, polls=None, *, reserve_per_day=RESERVE_PER_DAY):
    """CFBD calls this session may spend and the check interval, from the live remaining quota.

    Discretionary (game monitoring): spendable = remaining - (reserve_per_day x days until reset). Today's share is
    proportional to the games whose completion window falls in the next 24 hours, out of all games before the reset
    (at least an even daily share), and covers the releases due today when the spendable calls allow. Detection checks
    are spread over today's windows.

    Priority (releases): AP/Coaches and CFP releases due today may also draw on the reserve down to RELEASE_FLOOR
    (priority_budget), and so may one end-of-day publication wave for today's games when the discretionary budget
    cannot afford any. Release verification therefore never stops because the discretionary budget is empty.
    """
    remaining, reset = int(info["remainingCalls"]), cal.parse_time(info["resetAt"])
    days = max(1, math.ceil((reset - now).total_seconds() / 86400))
    spendable = max(0, remaining - reserve_per_day * days)
    pending = []
    for g in snapshot["games"]:
        k = cal.parse_time(g.get("start_date"))
        if not g.get("completed") and k and now <= k + cal.LATE_FINISH + cal.OVERDUE_LIMIT and k + cal.EARLY_FINISH < reset:
            pending.append(k)
    soon = [k for k in pending if k + cal.EARLY_FINISH <= now + timedelta(hours=24)]
    releases = releases_due_today(snapshot, polls, now)
    share = max(len(soon) / len(pending) if pending else 0, 1 / days)
    clusters = len({(k.date(), k.hour) for k in soon})
    cycle = 1 + REFRESH_COST                                # one check that finds finals + the refresh it triggers
    release_cost = (3 + POLL_REFRESH_COST) * (releases["polls"] + releases["cfp"])
    wanted = cycle * min(clusters, 3) + release_cost         # aim for at least three publication waves today
    budget = min(spendable, max(math.floor(spendable * share), wanted)) if (soon or release_cost) else 0
    games_budget = max(0, budget - release_cost)
    # Checks happen only inside completion windows (the calendar sleeps otherwise), so spread the affordable
    # check-and-refresh cycles over the total length of today's windows. A refresh publishes every final found so
    # far, so a tight quota means fewer, larger publication waves rather than no monitoring.
    windows = sorted((max(now, k + cal.EARLY_FINISH), k + cal.LATE_FINISH) for k in soon if k + cal.LATE_FINISH > now)
    covered, end = 0.0, None
    for a, b in windows:
        if end is None or a > end:
            covered += (b - a).total_seconds(); end = b
        elif b > end:
            covered += (b - end).total_seconds(); end = b
    cycles = games_budget // cycle
    if soon:
        interval = max(MIN_INTERVAL, covered / cycles) if cycles else None
    else:
        interval = max(MIN_INTERVAL, 5 * 3600 / 3) if release_cost and budget >= release_cost else None
    if interval is None:
        budget = 0
    # Priority allowance: releases first, then one end-of-day games wave if nothing else can publish today's finals.
    room = max(0, remaining - RELEASE_FLOOR)
    release_budget = min(room, CFP_RELEASE_COST * releases["cfp"] + POLL_RELEASE_COST * releases["polls"])
    wave_at = None
    if windows and not cycles and room - release_budget >= cycle:
        wave_at = max(b for _, b in windows)                 # after the last game of the day can have finished
        release_budget += cycle
    poll_interval = None
    if releases["polls"]:
        local = now.astimezone(cal.CENTRAL)
        start = max(now, local.replace(hour=12, minute=55, second=0, microsecond=0).astimezone(timezone.utc))
        window_end = local.replace(hour=16, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
        span = max(0.0, (window_end - start).total_seconds())
        poll_interval = round(max(MIN_INTERVAL, span / POLL_CHECKS)) if span else MIN_INTERVAL
    return {"remaining": remaining, "days_to_reset": days, "spendable": spendable, "share_today": round(share, 3),
            "budget": budget, "interval_seconds": round(interval) if interval else None,
            "priority_budget": release_budget, "release_floor": RELEASE_FLOOR,
            "wave_at": wave_at.isoformat() if wave_at else None, "poll_interval_seconds": poll_interval,
            "kickoff_clusters_today": clusters, "games_finishing_next_24h": len(soon), "releases_due_today": releases}


def chain_successor(providers, now, run_id, *, max_per_hour=MAX_STARTS_PER_HOUR):
    """Queue the next watcher run as soon as this one starts (it waits in the concurrency group until this run ends).

    Returns (action, detail). "duplicate" means another run is already watching and this one must exit; the other
    outcomes let this run watch. Never more than one queued successor; a start rate above max_per_hour (a crash
    loop) stops the chain and is reported."""
    runs = providers.watcher_runs()
    others = [r for r in runs if int(r.get("id", 0)) != int(run_id or 0)]
    if any(r.get("status") == "in_progress" and int(r["id"]) < int(run_id or 0) for r in others):
        return "duplicate", "an earlier watcher run is already in progress"
    if any(r.get("status") in WAITING_RUN for r in others):
        return "already queued", "a successor is already waiting"
    recent = [r for r in runs if (t := cal.parse_time(r.get("created_at"))) and t >= now - timedelta(hours=1)]
    if len(recent) > max_per_hour:
        return "rate-limited", f"{len(recent)} watcher starts in the last hour; chain stopped to avoid a loop"
    providers.dispatch("event-watcher.yml", {"dry_run": "false"})
    return "queued", "successor queued"


class Watcher:
    def __init__(self, snapshot, polls, providers, *, clock=utcnow, sleep=time.sleep, dry_run=False,
                 active_interval=cal.ACTIVE_INTERVAL, watch_interval=cal.WATCH_INTERVAL, cfbd_budget=400, log=print,
                 postseason=None, release_budget=0, known_teams=None, monitor=None, stay_alive=False,
                 poll_interval=None, wave_at=None):
        self.season = snapshot["season"]
        post = [dict(g, season_type="postseason") for g in (postseason or {}).get("games", [])]
        self.snapshot = {"season": self.season, "games": [dict(g) for g in snapshot["games"]] + post}
        self.games = {int(g["game_id"]): g for g in self.snapshot["games"]}
        self.polls = json.loads(json.dumps(polls or {}))
        self.p, self.clock, self.sleep, self.dry_run, self.log = providers, clock, sleep, dry_run, log
        self.active_interval, self.watch_interval, self.cfbd_budget = active_interval, watch_interval, cfbd_budget
        self.release_budget, self.release_spent = release_budget, 0
        self.known_teams = known_teams
        self.monitor, self.stay_alive = monitor, stay_alive
        self.poll_interval = poll_interval or active_interval
        self.wave_at, self.wave_done = wave_at, False
        self.events, self.seen = [], set()
        self.health = {"games": SourceHealth(), "rankings": SourceHealth(), "dispatch": SourceHealth(), "site": SourceHealth(),
                       "official": SourceHealth()}
        self.stale_signals = []
        self.alerts = []
        self._last_games_check = None
        self._next_games_check = None
        self._next_poll_check = None
        self._last_monitor = None
        self.cfp = {}                 # release day -> {rows, event, last_absent, attempts, next_page, next_confirm}
        self.dispatch_cost = 0

    @property
    def spent(self):
        return self.p.cfbd_calls + self.dispatch_cost

    @property
    def discretionary_spent(self):
        return self.spent - self.release_spent

    def can_check(self):
        return self.discretionary_spent + REFRESH_COST < self.cfbd_budget      # always keep enough for one refresh

    def priority_room(self, n):
        return self.release_spent + n <= self.release_budget

    def _alert(self, text):
        if text not in self.alerts:
            self.alerts.append(text)
            self.log(f"ALERT: {text}")

    # ---- detection -------------------------------------------------------------------------------------------
    def _add(self, kind, key, detail, source, available_after=None):
        if key in self.seen:
            return None
        self.seen.add(key)
        e = Event(kind, key, detail, self.clock(), source, available_after=available_after)
        self.events.append(e)
        self.log(f"{kind}: {detail}")
        return e

    def check_games(self, season_types=("regular",), priority=False):
        now = self.clock()
        h = self.health["games"]
        if not h.ok(now) or not (priority or self.can_check()):
            return []
        try:
            current = {}
            for kind in season_types:
                rows = self.p.games(self.season) if kind == "regular" else self.p.postseason(self.season)
                if priority:
                    self.release_spent += 1
                current.update(normalise(rows, self.season))
        except Exception as error:                      # outage, timeout, bad JSON: back off this source only
            h.fail(now, error, self.active_interval)
            self.log(f"games source failed ({h.failures}): {h.last_error}")
            return []
        h.recover()
        previous, self._last_games_check = self._last_games_check, now
        if not current:
            self.stale_signals.append({"at": now.isoformat(), "source": "games", "reason": "empty response"})
            return []
        finals = []
        for gid, game in self.games.items():
            src = current.get(gid)
            if src is None:
                continue
            if src["start_date"] and src["start_date"] != game.get("start_date") and not game.get("completed"):
                self._add("reschedule", f"reschedule:{gid}:{src['start_date']}", {"game_id": gid, "from": game.get("start_date"), "to": src["start_date"]}, "cfbd/games")
                game["start_date"] = src["start_date"]          # the calendar follows the new kickoff
            has_score = src["home_score"] is not None and src["away_score"] is not None
            if game.get("completed"):
                if not src["completed"] or not has_score:   # a final game reported as not final: stale, never regress
                    self.stale_signals.append({"at": now.isoformat(), "source": "games", "game_id": gid, "reason": "final game reported incomplete"})
                elif (src["home_score"], src["away_score"]) != (game.get("home_score"), game.get("away_score")):
                    e = self._add("correction", f"correction:{gid}:{src['home_score']}-{src['away_score']}",
                                  {"game_id": gid, "home": game.get("home"), "away": game.get("away"),
                                   "from": [game.get("home_score"), game.get("away_score")], "to": [src["home_score"], src["away_score"]]},
                                  "cfbd/games", previous)
                    if e:
                        e.priority = priority
                        finals.append(e)
                    game.update(home_score=src["home_score"], away_score=src["away_score"])
            elif src["completed"] and has_score:
                e = self._add("final", f"final:{gid}:{src['home_score']}-{src['away_score']}",
                              {"game_id": gid, "home": game.get("home"), "away": game.get("away"), "score": [src["home_score"], src["away_score"]],
                               "season_type": game.get("season_type", "regular")}, "cfbd/games", previous)
                if e:
                    e.priority = priority
                    finals.append(e)
                game.update(completed=True, home_score=src["home_score"], away_score=src["away_score"])
        return finals

    def check_polls(self, plan):
        """AP/Coaches releases from CFBD (no reliable machine-readable official source). Paid from the discretionary
        budget when it can afford it, otherwise from the release allowance, at most every poll_interval."""
        now = self.clock()
        h = self.health["rankings"]
        if not plan.polls_due or not h.ok(now) or (self._next_poll_check and now < self._next_poll_check):
            return []
        discretionary = self.discretionary_spent + POLL_REFRESH_COST < self.cfbd_budget
        priority = not discretionary and self.priority_room(1 + POLL_REFRESH_COST)
        if not (discretionary or priority):
            return []
        self._next_poll_check = now + timedelta(seconds=self.poll_interval if priority else min(self.poll_interval, self.active_interval))
        try:
            found = choose_polls(self.p.rankings(self.season))
        except Exception as error:
            h.fail(now, error, self.active_interval)
            self.log(f"rankings source failed ({h.failures}): {h.last_error}")
            return []
        finally:
            if priority:
                self.release_spent += 1
        h.recover()
        published = self.polls.setdefault("poll_weeks", {})
        out = []
        for key in plan.polls_due:
            week = found.get(key, (None,))[0]
            if week is None:
                continue
            if week < (published.get(key) or 0):
                self.stale_signals.append({"at": now.isoformat(), "source": "rankings", "poll": key, "reason": "older week than published"})
            elif week > (published.get(key) or 0):
                e = self._add("poll", f"poll:{key}:{week}", {"poll": key, "week": week}, "cfbd/rankings")
                if e:
                    e.priority = priority
                    out.append(e)
        return out

    def cfp_due(self, now):
        """The CFP release whose announcement time has passed, is not yet published and is still being watched."""
        published = self.polls.get("cfp_published_at")
        day = cfp_publish.due_release(now, date.fromisoformat(published) if published else None)
        if day is None or now > cfp_announcement(day) + CFP_WATCH_LIMIT:
            return None
        return day

    def check_cfp_official(self):
        """Read the dated official CFP page (no CFBD call); confirm a complete parse with one CFBD call."""
        now = self.clock()
        day = self.cfp_due(now)
        if day is None:
            return []
        st = self.cfp.setdefault(day, {"rows": None, "event": None, "last_absent": None, "attempts": 0,
                                       "next_page": None, "next_confirm": None})
        out = []
        if st["rows"] is None:
            h = self.health["official"]
            if not h.ok(now) or (st["next_page"] and now < st["next_page"]):
                return []
            st["next_page"] = now + timedelta(seconds=CFP_PAGE_INTERVAL)
            url = cfp_publish.official_url(day)
            try:
                html = self.p.cfp_page(url)
            except Exception as error:
                h.fail(now, error, CFP_PAGE_INTERVAL)
                self.log(f"official CFP page failed ({h.failures}): {h.last_error}")
                return []
            h.recover()
            if html is None:
                st["last_absent"] = now
                return []
            try:
                st["rows"] = cfp_publish.parse_official(html, day, self.known_teams or set())
            except cfp_publish.NotPublishable as reason:   # page exists but is not a complete dated release yet
                st["last_absent"] = now
                self.stale_signals.append({"at": now.isoformat(), "source": "official", "reason": str(reason)})
                return []
            st["event"] = self._add("cfp", f"cfp:{day.isoformat()}", {"release": day.isoformat(), "url": url},
                                    "official-page", st["last_absent"])
            if st["event"]:
                st["event"].priority = True
                out.append(st["event"])
        e = st["event"]
        if e is None or e.confirmed_at or st["attempts"] >= CFP_CONFIRM_MAX or (st["next_confirm"] and now < st["next_confirm"]):
            return out
        if not self.priority_room(1 + POLL_REFRESH_COST) and self.discretionary_spent + 1 + POLL_REFRESH_COST >= self.cfbd_budget:
            self._alert(f"official CFP {day.isoformat()} release found but no CFBD calls are left to confirm it; "
                        "the scheduled poll workflow will publish it when it runs")
            return out
        st["attempts"] += 1
        try:
            weeks = self.p.rankings(self.season)
            self.release_spent += 1
            week = cfp_publish.verify(st["rows"], cfp_publish.cfbd_committee(weeks), self.polls.get("cfp_week"))
        except cfp_publish.NotPublishable as reason:          # CFBD has not caught up yet: back off and retry
            st["next_confirm"] = now + timedelta(minutes=2 ** st["attempts"])
            self.log(f"CFP confirmation {st['attempts']}/{CFP_CONFIRM_MAX}: {reason}")
            if st["attempts"] >= CFP_CONFIRM_MAX:
                self._alert(f"official CFP {day.isoformat()} release is out but CFBD has not confirmed it after "
                            f"{CFP_CONFIRM_MAX} checks ({reason}); not published")
            return out
        except Exception as error:
            self.health["rankings"].fail(now, error, 60)
            st["next_confirm"] = now + timedelta(minutes=1)
            return out
        e.confirmed_at = now
        e.detail["week"] = week
        return out

    # ---- action and verification ----------------------------------------------------------------------------
    def dispatch(self, workflow, events, inputs=None):
        if not events:
            return
        now = self.clock()
        if self.dry_run:
            for e in events:
                e.status = "recorded"
            return
        h = self.health["dispatch"]
        if not h.ok(now):
            return                                       # retried on a later iteration (events stay "detected")
        try:
            self.p.dispatch(workflow, inputs)
        except Exception as error:
            h.fail(now, error, 60)
            self.log(f"dispatch {workflow} failed ({h.failures}): {h.last_error}")
            return
        h.recover()
        cost = REFRESH_COST if workflow == "refresh-data.yml" else POLL_REFRESH_COST
        self.dispatch_cost += cost
        if any(e.priority for e in events):
            self.release_spent += cost
        for e in events:
            e.dispatched_at, e.status, e.attempts = now, "dispatched", e.attempts + 1
            e.detail["workflow"] = workflow

    def verify(self):
        waiting = [e for e in self.events if e.status == "dispatched"]
        if not waiting:
            return
        now = self.clock()
        h = self.health["site"]
        if not h.ok(now):
            return
        try:
            report = self.p.live_report() if any(e.kind in ("final", "correction") and e.detail.get("season_type") != "postseason" for e in waiting) else None
            post = self.p.live_postseason() if any(e.detail.get("season_type") == "postseason" for e in waiting) else None
            polls = self.p.live_polls() if any(e.kind in ("poll", "cfp") for e in waiting) else None
        except Exception as error:
            h.fail(now, error, 60)
            return
        h.recover()
        live = {g["game_id"]: g for g in (report or {}).get("schedule", [])}
        live_post = {g["game_id"]: g for g in (post or {}).get("games", [])}
        for e in waiting:
            if e.kind in ("final", "correction"):
                g = (live_post if e.detail.get("season_type") == "postseason" else live).get(e.detail["game_id"])
                want = e.detail.get("score") or e.detail.get("to")
                ok = bool(g and g.get("completed") and [g.get("home_score"), g.get("away_score")] == want)
            elif e.kind == "cfp":
                ok = (polls or {}).get("cfp_published_at") == e.detail["release"]
                if ok:
                    self.polls.update(cfp_published_at=e.detail["release"], cfp_week=e.detail.get("week"))
            else:
                ok = ((polls or {}).get("poll_weeks", {}).get(e.detail["poll"]) or 0) >= e.detail["week"]
            if ok:
                e.published_at, e.status = now, "published"
            elif now - e.dispatched_at > VERIFY_TIMEOUT:
                if e.attempts < 2:
                    e.status = "detected"                # re-dispatch once
                else:
                    e.status = "alerted"
                    self._alert(f"{e.kind} {e.detail} not visible on the live site {VERIFY_TIMEOUT} after two refreshes")

    def redispatch(self):
        retry = [e for e in self.events if e.status == "detected" and e.kind in ("final", "correction")]
        self.dispatch("refresh-data.yml", retry, {"season": str(self.season)})
        # A CFP release is dispatched only once CFBD has confirmed the official page (cfp_publish re-checks both).
        retry_polls = [e for e in self.events if e.status == "detected" and (e.kind == "poll" or (e.kind == "cfp" and e.confirmed_at))]
        self.dispatch("refresh-polls.yml", retry_polls)

    # ---- loop ---------------------------------------------------------------------------------------------------
    def reconciling(self):
        now = self.clock()
        return any(e.kind in ("final", "correction") and now - e.detected_at <= RECONCILE_WINDOW for e in self.events)

    def awaiting(self):
        return any(e.status == "dispatched" or (e.status == "detected" and (e.kind != "cfp" or e.confirmed_at))
                   for e in self.events if e.kind in ("final", "correction", "poll", "cfp"))

    def next_cfp_wake(self, now):
        """Seconds until the next official-page read or confirmation retry, or None when no release is watched."""
        day = self.cfp_due(now)
        if day is None:
            upcoming = [cfp_announcement(d) for d in cal.cfp_release_days(now.year) if cfp_announcement(d) > now]
            return (min(upcoming) - now).total_seconds() if upcoming else None
        st = self.cfp.get(day)
        if st is None:
            return 0
        if st["rows"] is None:
            return max(0.0, ((st["next_page"] or now) - now).total_seconds())
        e = st["event"]
        if e and not e.confirmed_at and st["attempts"] < CFP_CONFIRM_MAX:
            return max(0.0, ((st["next_confirm"] or now) - now).total_seconds())
        return None

    def step(self):
        now = self.clock()
        plan = cal.plan(self.snapshot, self.polls, now, active_interval=self.active_interval, watch_interval=self.watch_interval)
        due_reconcile = self.reconciling() and (self._last_games_check is None or now - self._last_games_check >= timedelta(seconds=max(self.watch_interval, RECONCILE_INTERVAL)))
        timer_ok = self._next_games_check is None or now >= self._next_games_check
        wave = bool(self.wave_at and not self.wave_done and now >= self.wave_at and self.priority_room(1 + REFRESH_COST))
        finals = []
        if ((plan.monitors_games and timer_ok) or due_reconcile) and self.can_check() or wave:
            self._next_games_check = now + timedelta(seconds=plan.interval or self.watch_interval)
            watched = plan.games_due + plan.games_overdue
            kinds = {g.get("season_type", "regular") for g in watched} if watched else {"regular"}
            if due_reconcile:
                kinds |= {e.detail.get("season_type", "regular") for e in self.events if e.kind in ("final", "correction")}
            use_priority = wave and not self.can_check()
            finals = self.check_games(tuple(sorted(kinds, reverse=True)), priority=use_priority)
            self.wave_done = self.wave_done or use_priority
        polls = self.check_polls(plan)
        for e in polls:                                  # the poll workflow re-validates; mark expected week as seen
            self.polls["poll_weeks"][e.detail["poll"]] = e.detail["week"]
        cfp = self.check_cfp_official()
        self.redispatch()                                # includes the new events (status "detected")
        self.verify()
        if self.monitor and (self._last_monitor is None or now - self._last_monitor >= timedelta(seconds=MONITOR_INTERVAL)):
            self._last_monitor = now
            try:
                self.monitor(self)
            except Exception as error:                   # monitoring must never stop the watcher
                self.log(f"freshness monitor failed: {str(error)[:200]}")
        return plan, finals, polls + cfp

    def run(self, deadline):
        while True:
            plan, _, _ = self.step()
            now = self.clock()
            waits = []
            if plan.intensity != "idle" and (plan.monitors_games or plan.polls_due):
                waits.append(plan.interval)
            if self.awaiting():
                waits.append(VERIFY_POLL)                # dispatch retries and live-site verification
            if self.reconciling():
                waits.append(max(self.watch_interval, RECONCILE_INTERVAL))
            if plan.next_event_at and plan.next_event_at < deadline:
                waits.append((plan.next_event_at - now).total_seconds())
            if self.wave_at and not self.wave_done and self.wave_at > now:
                waits.append((self.wave_at - now).total_seconds())
            cfp_wake = self.next_cfp_wake(now)
            if cfp_wake is not None and now + timedelta(seconds=cfp_wake) < deadline:
                waits.append(cfp_wake)
            if self.stay_alive:
                waits.append(MONITOR_INTERVAL)           # a chained run stays alive until its deadline
            waits = [w for w in waits if w is not None]
            if not waits:
                break
            wait = min(waits)
            if self.dry_run or now + timedelta(seconds=wait) >= deadline:
                break
            self.sleep(max(VERIFY_POLL, wait))
        return self.report()

    def report(self):
        latencies = [e.record()["detection_to_publication_seconds"] for e in self.events if e.published_at]
        totals = [e.record()["total_seconds_at_most"] for e in self.events if e.published_at]
        within = sum(1 for s in totals if s <= 300)
        return {"generated_at": self.clock().isoformat(), "dry_run": self.dry_run, "cfbd_calls": self.p.cfbd_calls,
                "cfbd_calls_including_dispatched_refreshes": self.spent, "cfbd_budget": self.cfbd_budget,
                "priority_spent": self.release_spent, "priority_budget": self.release_budget,
                "events": [e.record() for e in self.events], "alerts": self.alerts, "stale_signals": self.stale_signals[-50:],
                "source_health": {k: {"failures": v.failures, "last_error": v.last_error} for k, v in self.health.items()},
                "latency": {"published": len(latencies), "within_5_minutes_total": within,
                            "median_detection_to_publication_seconds": sorted(latencies)[len(latencies) // 2] if latencies else None,
                            "median_total_seconds_at_most": sorted(totals)[len(totals) // 2] if totals else None}}


def cfp_announcement(day):
    """Scheduled announcement time of a CFP release (17:00 Central; 10:00 on selection Sunday), as cfp_publish uses."""
    return datetime(day.year, day.month, day.day, 10 if day.weekday() == 6 else 17, tzinfo=cal.CENTRAL).astimezone(timezone.utc)


def summary_markdown(result, plan):
    lines = ["## Event watcher", "", f"Plan at start: `{json.dumps(plan.summary())}`", "",
             f"Chain: {result.get('chain', 'not chained')}", "",
             f"CFBD calls: {result['cfbd_calls']} (priority {result.get('priority_spent', 0)}/{result.get('priority_budget', 0)})"
             f" · events: {len(result['events'])} · alerts: {len(result['alerts'])}", ""]
    if result["events"]:
        lines += ["| Event | Detail | Status | Detection (at most) | Verification | Publication | Total (at most) |",
                  "| --- | --- | --- | --- | --- | --- | --- |"]
        fmt = lambda s: "" if s is None else f"{s // 60}m {s % 60}s"
        for e in result["events"]:
            lines.append(f"| {e['kind']} | {json.dumps(e['detail'])} | {e['status']} | {fmt(e['detection_seconds_at_most'])} | "
                         f"{fmt(e['verification_seconds'])} | {fmt(e['publication_seconds'])} | {fmt(e['total_seconds_at_most'])} |")
    lines += [f"- ALERT: {a}" for a in result["alerts"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="check every real provider once; dispatch nothing")
    ap.add_argument("--minutes", type=float, default=350, help="run budget (GitHub job limit is 360)")
    ap.add_argument("--ledger", type=Path, default=Path("event-ledger.json"))
    args = ap.parse_args(argv)
    from . import freshness_monitor
    snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
    polls = json.loads(Path("data/poll-2026-snapshot.json").read_text())
    post_path = Path("data/cfbd-2026-postseason.json")
    postseason = json.loads(post_path.read_text()) if post_path.exists() else None
    known = {t["team"] for t in json.loads(Path("data/season-2026-report.json").read_text())["rankings"]}
    providers = Providers(os.environ.get("CFBD_API_KEY", ""), os.environ.get("GITHUB_TOKEN", ""))
    watcher = Watcher(snapshot, polls, providers, dry_run=args.dry_run, postseason=postseason, known_teams=known)
    now = utcnow()
    # The published snapshot can be newer than the checkout (a refresh committed after this run started).
    try:
        live = providers.live_polls()
        if (live.get("cfp_published_at") or "") > (watcher.polls.get("cfp_published_at") or ""):
            watcher.polls.update({k: live[k] for k in ("cfp_published_at", "cfp_week") if k in live})
    except Exception as error:
        print(f"live poll snapshot unavailable: {str(error)[:120]}")
    # Chain first, before any other work: the successor waits in the concurrency group until this run ends.
    chain = "not chained (dry run)" if args.dry_run else "not chained (no games left to watch)"
    if not args.dry_run and cal.horizon_active(watcher.snapshot, now):
        try:
            action, detail = chain_successor(providers, now, os.environ.get("GITHUB_RUN_ID", 0))
        except Exception as error:
            action, detail = "failed", f"could not queue a successor: {str(error)[:200]}"
        chain = f"{action}: {detail}"
        if action == "duplicate":
            print(f"chain: {chain}; exiting without watching")
            return
        if action in ("rate-limited", "failed"):
            watcher._alert(f"watcher chain {chain}")
        watcher.stay_alive = action in ("queued", "already queued")
    print("chain:", chain)
    # Pace CFBD calls to the live monthly quota; an unreadable quota falls back to a conservative session.
    try:
        quota = quota_plan(providers.info(), watcher.snapshot, now, watcher.polls)
    except Exception as error:
        quota = {"error": str(error)[:200], "budget": 12, "interval_seconds": 1800, "priority_budget": CFP_RELEASE_COST,
                 "poll_interval_seconds": None, "wave_at": None}
    watcher.cfbd_budget = min(int(os.environ.get("CFBD_CALL_BUDGET", 400)), quota["budget"])
    watcher.release_budget = quota.get("priority_budget", 0)
    watcher.wave_at = cal.parse_time(quota.get("wave_at"))
    if quota.get("interval_seconds"):
        watcher.active_interval = max(int(os.environ.get("WATCH_ACTIVE_SECONDS", MIN_INTERVAL)), quota["interval_seconds"])
    watcher.poll_interval = quota.get("poll_interval_seconds") or watcher.active_interval
    watcher.monitor = lambda w: freshness_monitor.run_pass(providers, now=w.clock(), snapshot=w.snapshot, quota=quota,
                                                           watcher_alerts=w.alerts, log=w.log)
    start_plan = cal.plan(watcher.snapshot, watcher.polls, now, active_interval=watcher.active_interval)
    print("plan:", json.dumps(start_plan.summary()))
    print("quota:", json.dumps(quota))
    if args.dry_run:
        def page(url):
            try:
                return providers.official_page(url)
            except Exception as error:
                if "404" in str(error):
                    return None
                raise
        latest_cfp = cfp_publish.release_dates()[0]
        for d in cfp_publish.release_dates():
            if cfp_announcement(d) <= now:
                latest_cfp = d
        checks = {}
        for name, call in (("cfbd_games", lambda: len(normalise(providers.games(watcher.season), watcher.season))),
                           ("cfbd_rankings", lambda: {k: v[0] for k, v in choose_polls(providers.rankings(watcher.season)).items()}),
                           ("cfbd_postseason", lambda: len(providers.postseason(watcher.season))),
                           ("cfbd_info", lambda: {k: v for k, v in providers.info().items() if k in ("tierName", "monthlyLimit", "remainingCalls", "usedCalls", "resetAt")}),
                           ("official_cfp_page_parse", lambda: len(cfp_publish.parse_official(page(cfp_publish.official_url(latest_cfp)) or "", latest_cfp, known))),
                           ("cfp_publish_would", lambda: cfp_publish.run(now, polls, known, fetch_page=page, fetch_rankings=lambda: providers.rankings(watcher.season))[2]),
                           ("github_workflows", lambda: sorted(w["path"].split("/")[-1] for w in providers.workflows()["workflows"]
                                                               if w["path"].endswith(("refresh-data.yml", "refresh-polls.yml", "event-watcher.yml")))),
                           ("github_watcher_runs", lambda: len(providers.watcher_runs())),
                           ("live_report", lambda: providers.live_report()["retrieved_at"]),
                           ("live_polls", lambda: providers.live_polls().get("poll_weeks"))):
            started = time.monotonic()
            try:
                checks[name] = {"ok": True, "value": call(), "seconds": round(time.monotonic() - started, 2)}
            except Exception as error:
                checks[name] = {"ok": False, "error": str(error)[:200], "seconds": round(time.monotonic() - started, 2)}
        result = {**watcher.report(), "quota": quota, "provider_checks": checks}
    elif watcher.cfbd_budget <= 0 and watcher.release_budget <= 0 and not watcher.stay_alive and watcher.cfp_due(now) is None:
        watcher._alert(f"Monitoring paused to protect the CFBD quota ({quota.get('remaining')} calls left, "
                       f"{quota.get('days_to_reset')} days to reset); the daily baseline refresh still reconciles results")
        result = {**watcher.report(), "quota": quota}
    else:
        if watcher.cfbd_budget <= 0:
            print(f"Discretionary CFBD budget exhausted ({quota.get('remaining')} calls left, "
                  f"{quota.get('days_to_reset')} days to reset): official CFP pages are still read every "
                  f"{CFP_PAGE_INTERVAL} s and releases use the priority allowance ({watcher.release_budget} calls)")
        result = {**watcher.run(now + timedelta(minutes=args.minutes)), "quota": quota}
    result["chain"] = chain
    args.ledger.write_text(json.dumps(result, indent=1, default=str))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(summary_markdown(result, start_plan) + f"\nQuota: `{json.dumps(quota)}`\n")
    for alert in result["alerts"]:
        print(f"::warning::{alert}")
    print(json.dumps({k: result[k] for k in ("cfbd_calls", "latency", "alerts", "chain")} | ({"provider_checks": result["provider_checks"]} if "provider_checks" in result else {}), indent=1))
    if args.dry_run and not all(c["ok"] for c in result["provider_checks"].values()):
        raise SystemExit("a provider check failed")


if __name__ == "__main__":
    main()
