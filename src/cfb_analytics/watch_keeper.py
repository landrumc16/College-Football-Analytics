"""Keep the event watcher running and report freshness problems, from any workflow run.

  python -m cfb_analytics.watch_keeper     # run after the data refresh, poll refresh, deployment and watcher jobs

GitHub's scheduler has started runs many hours late, so the watcher chain must not depend on it. Every workflow that
runs for another reason (a data commit, a deployment, a poll check) also checks that a watcher is running or queued while
games or releases are due, restarts the chain if it has stopped (rate-capped, never a second concurrent watcher), and
runs one freshness monitor pass. No CFBD calls.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import event_calendar as cal
from . import freshness_monitor
from .event_watcher import ACTIVE_RUN, MAX_STARTS_PER_HOUR, Providers

HANDOFF_GRACE = freshness_monitor.HANDOFF_GRACE


def ensure_watcher(runs, now, needed, dispatch, *, max_per_hour=MAX_STARTS_PER_HOUR, me=None):
    """Restart the watcher chain when monitoring is needed and no watcher is running or queued. Returns the action.
    `me` is the calling run's id: a watcher job checking at its own end does not count itself as the chain."""
    runs = [r for r in runs if me is None or int(r.get("id", 0)) != int(me)]
    if not needed:
        return "not needed: nothing due within 48 hours"
    if any(r.get("status") in ACTIVE_RUN for r in runs):
        return "watcher running or queued"
    ended = [t for r in runs if (t := cal.parse_time(r.get("updated_at")))]
    if ended and now - max(ended) < HANDOFF_GRACE:
        return "handoff in progress"
    recent = [r for r in runs if (t := cal.parse_time(r.get("created_at"))) and t >= now - timedelta(hours=1)]
    if len(recent) > max_per_hour:
        return f"not restarted: {len(recent)} watcher starts in the last hour (possible crash loop)"
    dispatch("event-watcher.yml", {"dry_run": "false"})
    return "restarted the watcher chain"


def load_snapshot():
    snapshot = json.loads(Path("data/cfbd-2026-games.json").read_text())
    post = Path("data/cfbd-2026-postseason.json")
    if post.exists():
        snapshot = {**snapshot, "games": snapshot["games"] + [dict(g, season_type="postseason") for g in json.loads(post.read_text()).get("games", [])]}
    return snapshot


def main():
    providers = Providers(os.environ.get("CFBD_API_KEY", ""), os.environ.get("GITHUB_TOKEN", ""))
    now = datetime.now(timezone.utc)
    snapshot = load_snapshot()
    try:
        action = ensure_watcher(providers.watcher_runs(), now, cal.horizon_active(snapshot, now), providers.dispatch,
                                me=os.environ.get("GITHUB_RUN_ID"))
    except Exception as error:
        action = f"could not check the watcher: {str(error)[:200]}"
    print(f"keeper: {action}")
    alerts = freshness_monitor.run_pass(providers, now=now, snapshot=snapshot, watcher_running=action.startswith(("watcher running", "restarted", "handoff")))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(f"## Freshness keeper\n\n{action}\n\n" + "".join(f"- **{a['severity']}** {a['area']}: {a['text']}\n" for a in alerts))
    for a in alerts:
        print(f"::warning::{a['area']}: {a['text']}")


if __name__ == "__main__":
    main()
