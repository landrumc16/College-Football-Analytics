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
CFBD call budget is capped per run. CFP releases are detected and alerted for manual verification only, matching the
existing rule that undated CFP feed rows are never published as official.
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

    def record(self):
        lat = lambda a, b: round((b - a).total_seconds()) if a and b else None
        return {"kind": self.kind, "key": self.key, "detail": self.detail, "source": self.source, "status": self.status,
                "detected_at": self.detected_at.isoformat(), "dispatched_at": self.dispatched_at and self.dispatched_at.isoformat(),
                "published_at": self.published_at and self.published_at.isoformat(), "attempts": self.attempts,
                "detection_to_publication_seconds": lat(self.detected_at, self.published_at)}


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

    Spendable = remaining - (reserve_per_day x days until reset). Today's share is proportional to the games whose
    completion window falls in the next 24 hours, out of all games before the reset (at least an even daily share),
    and always covers the releases due today (a refresh per kickoff cluster, a poll refresh, a few checks) when the
    spendable calls allow. Detection checks are spread over today's windows.
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
    return {"remaining": remaining, "days_to_reset": days, "spendable": spendable, "share_today": round(share, 3),
            "budget": budget, "interval_seconds": round(interval) if interval else None,
            "kickoff_clusters_today": clusters, "games_finishing_next_24h": len(soon), "releases_due_today": releases}


class Watcher:
    def __init__(self, snapshot, polls, providers, *, clock=utcnow, sleep=time.sleep, dry_run=False,
                 active_interval=cal.ACTIVE_INTERVAL, watch_interval=cal.WATCH_INTERVAL, cfbd_budget=400, log=print,
                 postseason=None):
        self.season = snapshot["season"]
        post = [dict(g, season_type="postseason") for g in (postseason or {}).get("games", [])]
        self.snapshot = {"season": self.season, "games": [dict(g) for g in snapshot["games"]] + post}
        self.games = {int(g["game_id"]): g for g in self.snapshot["games"]}
        self.polls = json.loads(json.dumps(polls or {}))
        self.p, self.clock, self.sleep, self.dry_run, self.log = providers, clock, sleep, dry_run, log
        self.active_interval, self.watch_interval, self.cfbd_budget = active_interval, watch_interval, cfbd_budget
        self.events, self.seen = [], set()
        self.health = {"games": SourceHealth(), "rankings": SourceHealth(), "dispatch": SourceHealth(), "site": SourceHealth()}
        self.stale_signals = []
        self.alerts = []
        self._last_games_check = None
        self.dispatch_cost = 0

    @property
    def spent(self):
        return self.p.cfbd_calls + self.dispatch_cost

    def can_check(self):
        return self.spent + REFRESH_COST < self.cfbd_budget      # always keep enough for one refresh

    # ---- detection -------------------------------------------------------------------------------------------
    def _add(self, kind, key, detail, source):
        if key in self.seen:
            return None
        self.seen.add(key)
        e = Event(kind, key, detail, self.clock(), source)
        self.events.append(e)
        self.log(f"{kind}: {detail}")
        return e

    def check_games(self, season_types=("regular",)):
        now = self.clock()
        h = self.health["games"]
        if not h.ok(now) or not self.can_check():
            return []
        try:
            current = {}
            for kind in season_types:
                rows = self.p.games(self.season) if kind == "regular" else self.p.postseason(self.season)
                current.update(normalise(rows, self.season))
        except Exception as error:                      # outage, timeout, bad JSON: back off this source only
            h.fail(now, error, self.active_interval)
            self.log(f"games source failed ({h.failures}): {h.last_error}")
            return []
        h.recover()
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
                                   "from": [game.get("home_score"), game.get("away_score")], "to": [src["home_score"], src["away_score"]]}, "cfbd/games")
                    if e:
                        finals.append(e)
                    game.update(home_score=src["home_score"], away_score=src["away_score"])
            elif src["completed"] and has_score:
                e = self._add("final", f"final:{gid}:{src['home_score']}-{src['away_score']}",
                              {"game_id": gid, "home": game.get("home"), "away": game.get("away"), "score": [src["home_score"], src["away_score"]],
                               "season_type": game.get("season_type", "regular")}, "cfbd/games")
                if e:
                    finals.append(e)
                game.update(completed=True, home_score=src["home_score"], away_score=src["away_score"])
        return finals

    def check_polls(self, plan):
        now = self.clock()
        h = self.health["rankings"]
        if not (plan.polls_due or plan.cfp_due) or not h.ok(now) or self.spent + POLL_REFRESH_COST >= self.cfbd_budget:
            return []
        try:
            found = choose_polls(self.p.rankings(self.season))
        except Exception as error:
            h.fail(now, error, self.active_interval)
            self.log(f"rankings source failed ({h.failures}): {h.last_error}")
            return []
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
                    out.append(e)
        if plan.cfp_due and "cfp_top25" in found and found["cfp_top25"][0] > (self.polls.get("cfp_week") or 0):
            # The poll workflow publishes it only if the dated official release confirms it (cfp_publish).
            e = self._add("cfp", f"cfp:{found['cfp_top25'][0]}", {"week": found["cfp_top25"][0]}, "cfbd/rankings")
            if e:
                out.append(e)
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
        self.dispatch_cost += REFRESH_COST if workflow == "refresh-data.yml" else POLL_REFRESH_COST
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
                ok = ((polls or {}).get("cfp_week") or 0) >= e.detail["week"] and bool((polls or {}).get("cfp_published_at"))
            else:
                ok = ((polls or {}).get("poll_weeks", {}).get(e.detail["poll"]) or 0) >= e.detail["week"]
            if ok:
                e.published_at, e.status = now, "published"
            elif now - e.dispatched_at > VERIFY_TIMEOUT:
                if e.attempts < 2:
                    e.status = "detected"                # re-dispatch once
                else:
                    e.status = "alerted"
                    self.alerts.append(f"{e.kind} {e.detail} not visible on the live site {VERIFY_TIMEOUT} after two refreshes")

    def redispatch(self):
        retry = [e for e in self.events if e.status == "detected" and e.kind in ("final", "correction")]
        self.dispatch("refresh-data.yml", retry, {"season": str(self.season)})
        retry_polls = [e for e in self.events if e.status == "detected" and e.kind in ("poll", "cfp")]
        self.dispatch("refresh-polls.yml", retry_polls)

    # ---- loop ---------------------------------------------------------------------------------------------------
    def reconciling(self):
        now = self.clock()
        return any(e.kind in ("final", "correction") and now - e.detected_at <= RECONCILE_WINDOW for e in self.events)

    def awaiting(self):
        return any(e.status in ("detected", "dispatched") and e.kind in ("final", "correction", "poll", "cfp") for e in self.events)

    def step(self):
        plan = cal.plan(self.snapshot, self.polls, self.clock(), active_interval=self.active_interval, watch_interval=self.watch_interval)
        now = self.clock()
        due_reconcile = self.reconciling() and (self._last_games_check is None or now - self._last_games_check >= timedelta(seconds=max(self.watch_interval, RECONCILE_INTERVAL)))
        finals = []
        if plan.monitors_games or due_reconcile:
            self._last_games_check = now
            watched = plan.games_due + plan.games_overdue
            kinds = {g.get("season_type", "regular") for g in watched} if watched else {"regular"}
            if due_reconcile:
                kinds |= {e.detail.get("season_type", "regular") for e in self.events if e.kind in ("final", "correction")}
            finals = self.check_games(tuple(sorted(kinds, reverse=True)))
        polls = self.check_polls(plan)
        for e in polls:                                  # the poll workflow re-validates; mark expected week as seen
            if e.kind == "poll":
                self.polls["poll_weeks"][e.detail["poll"]] = e.detail["week"]
            else:
                self.polls["cfp_week"] = e.detail["week"]
        self.redispatch()                                # includes the new events (status "detected")
        self.verify()
        return plan, finals, polls

    def run(self, deadline):
        while True:
            plan, _, _ = self.step()
            now = self.clock()
            if plan.intensity != "idle":
                wait = plan.interval
            elif self.awaiting():
                wait = 60                                # dispatch retries and live-site verification
            elif self.reconciling():
                wait = max(self.watch_interval, RECONCILE_INTERVAL)
            elif plan.next_event_at and plan.next_event_at < deadline:
                wait = (plan.next_event_at - now).total_seconds()
            else:
                break
            if self.dry_run or now + timedelta(seconds=wait) >= deadline:
                break
            self.sleep(max(30, wait))
        return self.report()

    def report(self):
        latencies = [e.record()["detection_to_publication_seconds"] for e in self.events if e.published_at]
        within = sum(1 for s in latencies if s <= 300)
        return {"generated_at": self.clock().isoformat(), "dry_run": self.dry_run, "cfbd_calls": self.p.cfbd_calls,
                "cfbd_calls_including_dispatched_refreshes": self.spent, "cfbd_budget": self.cfbd_budget,
                "events": [e.record() for e in self.events], "alerts": self.alerts, "stale_signals": self.stale_signals[-50:],
                "source_health": {k: {"failures": v.failures, "last_error": v.last_error} for k, v in self.health.items()},
                "latency": {"published": len(latencies), "within_5_minutes": within,
                            "median_seconds": sorted(latencies)[len(latencies) // 2] if latencies else None}}


def summary_markdown(result, plan):
    lines = ["## Event watcher", "", f"Plan at start: `{json.dumps(plan.summary())}`", "",
             f"CFBD calls: {result['cfbd_calls']} · events: {len(result['events'])} · alerts: {len(result['alerts'])}", ""]
    if result["events"]:
        lines += ["| Event | Detail | Status | Detection → live |", "| --- | --- | --- | --- |"]
        for e in result["events"]:
            s = e["detection_to_publication_seconds"]
            lines.append(f"| {e['kind']} | {json.dumps(e['detail'])} | {e['status']} | {'' if s is None else f'{s // 60}m {s % 60}s'} |")
    lines += [f"- ALERT: {a}" for a in result["alerts"]]
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="check every real provider once; dispatch nothing")
    ap.add_argument("--minutes", type=float, default=350, help="run budget (GitHub job limit is 360)")
    ap.add_argument("--ledger", type=Path, default=Path("event-ledger.json"))
    args = ap.parse_args(argv)
    snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
    polls = json.loads(Path("data/poll-2026-snapshot.json").read_text())
    post_path = Path("data/cfbd-2026-postseason.json")
    postseason = json.loads(post_path.read_text()) if post_path.exists() else None
    providers = Providers(os.environ.get("CFBD_API_KEY", ""), os.environ.get("GITHUB_TOKEN", ""))
    watcher = Watcher(snapshot, polls, providers, dry_run=args.dry_run, postseason=postseason)
    now = utcnow()
    # Pace CFBD calls to the live monthly quota; an unreadable quota falls back to a conservative session.
    try:
        quota = quota_plan(providers.info(), watcher.snapshot, now, watcher.polls)
    except Exception as error:
        quota = {"error": str(error)[:200], "budget": 12, "interval_seconds": 1800}
    watcher.cfbd_budget = min(int(os.environ.get("CFBD_CALL_BUDGET", 400)), quota["budget"])
    if quota.get("interval_seconds"):
        watcher.active_interval = max(int(os.environ.get("WATCH_ACTIVE_SECONDS", MIN_INTERVAL)), quota["interval_seconds"])
    start_plan = cal.plan(watcher.snapshot, watcher.polls, now, active_interval=watcher.active_interval)
    print("plan:", json.dumps(start_plan.summary()))
    print("quota:", json.dumps(quota))
    if args.dry_run:
        from . import cfp_publish
        known = {t["team"] for t in json.loads(Path("data/season-2026-report.json").read_text())["rankings"]}
        def page(url):
            try:
                return providers.official_page(url)
            except Exception as error:
                if "404" in str(error):
                    return None
                raise
        checks = {}
        for name, call in (("cfbd_games", lambda: len(normalise(providers.games(watcher.season), watcher.season))),
                           ("cfbd_rankings", lambda: {k: v[0] for k, v in choose_polls(providers.rankings(watcher.season)).items()}),
                           ("cfbd_postseason", lambda: len(providers.postseason(watcher.season))),
                           ("cfbd_info", lambda: {k: v for k, v in providers.info().items() if k in ("tierName", "monthlyLimit", "remainingCalls", "usedCalls", "resetAt")}),
                           ("cfp_publish_would", lambda: cfp_publish.run(now, polls, known, fetch_page=page, fetch_rankings=lambda: providers.rankings(watcher.season))[2]),
                           ("github_workflows", lambda: sorted(w["path"].split("/")[-1] for w in providers.workflows()["workflows"]
                                                               if w["path"].endswith(("refresh-data.yml", "refresh-polls.yml")))),
                           ("live_report", lambda: providers.live_report()["retrieved_at"]),
                           ("live_polls", lambda: providers.live_polls().get("poll_weeks"))):
            started = time.monotonic()
            try:
                checks[name] = {"ok": True, "value": call(), "seconds": round(time.monotonic() - started, 2)}
            except Exception as error:
                checks[name] = {"ok": False, "error": str(error)[:200], "seconds": round(time.monotonic() - started, 2)}
        result = {**watcher.report(), "quota": quota, "provider_checks": checks}
    elif watcher.cfbd_budget <= 0:
        watcher.alerts.append(f"Monitoring paused to protect the CFBD quota ({quota.get('remaining')} calls left, "
                              f"{quota.get('days_to_reset')} days to reset); the daily baseline refresh still reconciles results")
        result = {**watcher.report(), "quota": quota}
    else:
        result = {**watcher.run(now + timedelta(minutes=args.minutes)), "quota": quota}
    args.ledger.write_text(json.dumps(result, indent=1))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(summary_markdown(result, start_plan) + f"\nQuota: `{json.dumps(quota)}`\n")
    for alert in result["alerts"]:
        print(f"::warning::{alert}")
    print(json.dumps({k: result[k] for k in ("cfbd_calls", "latency", "alerts")} | ({"provider_checks": result["provider_checks"]} if "provider_checks" in result else {}), indent=1))
    if args.dry_run and not all(c["ok"] for c in result["provider_checks"].values()):
        raise SystemExit("a provider check failed")


if __name__ == "__main__":
    main()
