"""Automatic CFP publication: only dated, complete, independently confirmed official releases are published."""
import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from cfb_analytics import cfp_publish as cp

# Text of the official November 17, 2026 release as captured from collegefootballplayoff.com by the watcher dry run.
TABLE = ("CFP Selection Committee Completes Its Third Rankings of 2026 11/17/2026 8:46:00 PM | Football Share: "
         "CFP SELECTION COMMITTEE RANKINGS GAMES PLAYED THROUGH SUNDAY, NOVEMBER 15 CURRENT RANK CHANGE PREV. RANK TEAM "
         "OVERALL RECORD 1 -- 1 Georgia 9-1 2 -- 2 Utah 10-0 3 -- 3 Alabama 8-2 4 -- 4 UCLA 10-0 5 ▲1 6 Texas 8-2 "
         "6 ▼1 5 Notre Dame 9-1 7 -- 7 Miami 9-1 8 ▲1 9 Indiana 9-1 9 ▼1 8 Tennessee 8-2 10 -- 10 BYU 8-2 "
         "11 ▲2 13 Wake Forest 9-1 12 -- 12 Texas Tech 9-1 13 ▲3 16 Oregon 7-3 14 ▲6 20 Ohio State 7-3 15 -- 15 Iowa 8-2 "
         "16 ▼5 11 Kentucky 7-3 17 ▲7 24 Boise State 9-1 18 -- 18 USC 7-3 19 ▲4 23 Arizona 7-3 20 ▼6 14 Houston 7-3 "
         "21 ▼4 17 South Carolina 6-4 22 NEW NR Oklahoma 6-4 23 NEW NR Louisville 7-3 24 NEW NR Florida 6-4 "
         "25 ▼6 19 Ole Miss 6-4 Previous Rank = Tuesday, November 10 release.")
HTML = "<html><body><nav>CFP News 1 -- 1 Fake 1-1</nav><div>" + TABLE.replace(" | ", " <span>|</span> ") + "</div></body></html>"
OFFICIAL = [cp.canonical(t) for t in ("Georgia Utah Alabama UCLA Texas|Notre Dame|Miami|Indiana|Tennessee|BYU|Wake Forest|Texas Tech|"
                                       "Oregon|Ohio State|Iowa|Kentucky|Boise State|USC|Arizona|Houston|South Carolina|Oklahoma|"
                                       "Louisville|Florida|Ole Miss").replace("Georgia Utah Alabama UCLA ", "Georgia|Utah|Alabama|UCLA|").split("|")]
KNOWN = set(OFFICIAL) | {"LSU", "Missouri"}
NOV17 = date(2026, 11, 17)


def cfbd(week, teams):
    return [{"season": 2026, "week": week, "polls": [{"poll": "Playoff Committee Rankings",
                                                      "ranks": [{"rank": i + 1, "school": t} for i, t in enumerate(teams)]}]}]


CFBD_NAMES = ["Miami" if t == "Miami (FL)" else t for t in OFFICIAL]
SNAP = {"season": 2026, "poll_weeks": {"ap_top25": 12, "coaches_top25": 12}, "cfp_published_at": "2026-11-10", "cfp_week": 11,
        "cfp_source": "https://collegefootballplayoff.com/news/2026/11/10/rankings", "cfp_top25": []}
AFTER = datetime(2026, 11, 18, 3, 0, tzinfo=timezone.utc)      # Nov 17, 21:00 Central


def test_parses_the_real_official_release_and_ignores_navigation_text():
    rows = cp.parse_official(HTML, NOV17, KNOWN)
    assert [r["rank"] for r in rows] == list(range(1, 26))
    assert rows[6] == {"rank": 7, "team": "Miami (FL)", "record": "9-1"}       # official "Miami" -> app identity
    assert rows[11]["team"] == "Texas Tech" and rows[21]["team"] == "Oklahoma"


@pytest.mark.parametrize("html,reason", [
    (HTML.replace("11/17/2026", "11/10/2026"), "release date"),                # wrong or missing date
    (HTML.replace("TEAM OVERALL RECORD", "TEAM RECORD"), "table not found"),
    (HTML.replace("25 ▼6 19 Ole Miss 6-4", ""), "24 of 25"),                   # incomplete
    (HTML.replace("Ole Miss", "Georgia"), "twice"),                            # duplicate team
    (HTML.replace("Ole Miss", "Mystery U"), "not recognised"),                 # unknown team
])
def test_rejects_undated_incomplete_or_unrecognised_pages(html, reason):
    with pytest.raises(cp.NotPublishable, match=reason):
        cp.parse_official(html, NOV17, KNOWN)


def test_due_release_follows_the_official_schedule():
    assert cp.due_release(datetime(2026, 11, 17, 20, 0, tzinfo=timezone.utc), date(2026, 11, 10)) is None   # 14:00 Central
    assert cp.due_release(AFTER, date(2026, 11, 10)) == NOV17
    assert cp.due_release(AFTER, NOV17) is None                                                        # already published
    assert cp.due_release(datetime(2026, 12, 6, 17, 0, tzinfo=timezone.utc), date(2026, 12, 1)) == date(2026, 12, 6)


def test_publishes_only_when_cfbd_independently_confirms_the_same_week_order():
    updated, evidence, message = cp.run(AFTER, SNAP, KNOWN, fetch_page=lambda url: HTML, fetch_rankings=lambda: cfbd(12, CFBD_NAMES))
    assert message == "published the 2026-11-17 release (week 12)"
    assert updated["cfp_published_at"] == "2026-11-17" and updated["cfp_week"] == 12
    assert updated["cfp_source"] == "https://collegefootballplayoff.com/news/2026/11/17/rankings"
    assert updated["cfp_top25"][6] == {"team": "Miami (FL)", "rank": 7} and updated["poll_weeks"] == SNAP["poll_weeks"]
    assert evidence["kind"] == "official_current_cfp_publication" and len(evidence["rankings"]) == 25
    assert evidence["source_title"] == "CFP Selection Committee Completes Its Third Rankings of 2026"


def test_never_publishes_unconfirmed_stale_or_missing_releases():
    swapped = CFBD_NAMES[:]; swapped[0], swapped[1] = swapped[1], swapped[0]
    for rankings, why in ((lambda: cfbd(12, swapped), "disagree"), (lambda: cfbd(11, CFBD_NAMES), "not newer"),
                          (lambda: [], "no complete")):
        updated, _, message = cp.run(AFTER, SNAP, KNOWN, fetch_page=lambda url: HTML, fetch_rankings=rankings)
        assert updated is None and message.startswith("NOT PUBLISHED") and why in message, message
    updated, _, message = cp.run(AFTER, SNAP, KNOWN, fetch_page=lambda url: None, fetch_rankings=lambda: cfbd(12, CFBD_NAMES))
    assert updated is None and "not published yet" in message


def test_published_snapshot_is_retained_by_poll_refresh():
    from cfb_analytics.poll_refresh import retained_verified_cfp
    updated, _, _ = cp.run(AFTER, SNAP, KNOWN, fetch_page=lambda url: HTML, fetch_rankings=lambda: cfbd(12, CFBD_NAMES))
    kept = retained_verified_cfp(updated)
    assert kept["cfp_published_at"] == "2026-11-17" and len(kept["cfp_top25"]) == 25


def test_committed_snapshot_names_are_app_identities():
    report = {t["team"] for t in json.loads(Path("data/season-2026-report.json").read_text())["rankings"]}
    assert set(OFFICIAL) <= report
