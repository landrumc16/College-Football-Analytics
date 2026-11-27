"""Publish official CFP rankings automatically, only when they are authoritative, dated and independently confirmed.

  python -m cfb_analytics.cfp_publish     # run by refresh-polls.yml after poll_refresh

A release is published only if every check passes:
1. The official page for a scheduled release date (collegefootballplayoff.com/news/YYYY/MM/DD/rankings) exists and
   states that date.
2. It parses to exactly ranks 1-25 with 25 distinct teams that are all known FBS programs.
3. CFBD's "Playoff Committee Rankings" for its newest week list the same 25 teams in the same order (an independent
   source confirming the parse).
4. It is newer than the release already published.

Otherwise nothing changes and a warning names the failed check. Undated or unconfirmed rankings are never published,
which keeps poll_refresh's rule (CFBD rows alone are never dated as official). Each publication writes an evidence
file in the same format as the reviewed November 10 release.
"""
import hashlib
import html as htmllib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request
from .quota_client import urlopen
from zoneinfo import ZoneInfo

from .poll_refresh import CFP_DATES

SNAPSHOT = Path("data/poll-2026-snapshot.json")
EVIDENCE_DIR = Path("docs/evidence")
REPORT = Path("data/season-2026-report.json")
SEASON = 2026
ALIASES = {"Miami": "Miami (FL)", "App State": "Appalachian State", "Sam Houston": "Sam Houston State", "UL Monroe": "ULM"}
ROW = re.compile(r"(?<!\d)(\d{1,2}) (?:--|–|—|-|NEW|▲ ?\d{1,2}|▼ ?\d{1,2}) (?:\d{1,2}|NR) (.+?) (\d{1,2}-\d{1,2})(?=\s|$)")


class NotPublishable(Exception):
    pass


def release_dates(season=SEASON):
    return sorted(date(season, m, d) for m, d in CFP_DATES)


def official_url(day):
    return f"https://collegefootballplayoff.com/news/{day.year}/{day.month:02d}/{day.day:02d}/rankings"


def due_release(now, published, season=SEASON):
    """Latest release whose announcement time (17:00 Central; 10:00 on selection Sunday) has passed and that is newer
    than the published one."""
    local = now.astimezone(ZoneInfo("America/Chicago"))
    due = [d for d in release_dates(season)
           if (local.date(), local.hour) >= (d, 10 if d.weekday() == 6 else 17)]
    latest = due[-1] if due else None
    return latest if latest and (published is None or latest > published) else None


def page_text(html):
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", text))).strip()


def canonical(name):
    return ALIASES.get(name.strip(), name.strip())


def parse_official(html, day, known_teams):
    """[{rank, team, record}] for ranks 1-25 from the official page, or NotPublishable."""
    text = page_text(html)
    if f"{day.month}/{day.day}/{day.year}" not in text and f"{day.month:02d}/{day.day:02d}/{day.year}" not in text:
        raise NotPublishable(f"official page does not state the {day.isoformat()} release date")
    start = text.find("TEAM OVERALL RECORD")
    if start < 0:
        raise NotPublishable("official rankings table not found")
    rows, expected = [], 1
    for m in ROW.finditer(text, start):
        rank = int(m.group(1))
        if rank != expected:
            if rows:
                break
            continue
        rows.append({"rank": rank, "team": canonical(m.group(2)), "record": m.group(3)})
        expected += 1
        if expected > 25:
            break
    if [r["rank"] for r in rows] != list(range(1, 26)):
        raise NotPublishable(f"official page parsed {len(rows)} of 25 ranks")
    teams = [r["team"] for r in rows]
    if len(set(teams)) != 25:
        raise NotPublishable("official page lists a team twice")
    unknown = [t for t in teams if t not in known_teams]
    if unknown:
        raise NotPublishable(f"official teams not recognised as FBS programs: {unknown}")
    return rows


def cfbd_committee(weeks):
    """(week, [team, ...]) for CFBD's newest complete Playoff Committee Rankings."""
    best = None
    for entry in weeks or []:
        for poll in entry.get("polls", []):
            if "playoff" not in str(poll.get("poll", "")).lower():
                continue
            ranks = sorted(poll.get("ranks", []), key=lambda r: r.get("rank", 99))
            if [r.get("rank") for r in ranks] != list(range(1, 26)):
                continue
            if best is None or entry.get("week", 0) > best[0]:
                best = (entry.get("week"), [canonical(str(r.get("school", ""))) for r in ranks])
    if best is None:
        raise NotPublishable("CFBD has no complete Playoff Committee Rankings to confirm against")
    return best


def verify(official_rows, cfbd_week_teams, published_week):
    week, teams = cfbd_week_teams
    if published_week is not None and week <= published_week:
        raise NotPublishable(f"CFBD's newest committee week ({week}) is not newer than the published week ({published_week})")
    mismatches = [(r["rank"], r["team"], c) for r, c in zip(official_rows, teams) if r["team"] != c]
    if mismatches:
        raise NotPublishable(f"official page and CFBD disagree at {len(mismatches)} positions, e.g. {mismatches[:3]}")
    return week


def publish(snapshot, rows, week, day, url, title):
    """Updated snapshot and evidence record (same shape as the reviewed November 10 evidence)."""
    pairs = "\n".join(f"{r['rank']}|{r['team']}" for r in rows)
    updated = {**snapshot, "cfp_top25": [{"team": r["team"], "rank": r["rank"]} for r in rows],
               "cfp_published_at": day.isoformat(), "cfp_week": week, "cfp_source": url}
    evidence = {"kind": "official_current_cfp_publication", "season": SEASON, "week": week, "published_at": day.isoformat(),
                "source_url": url, "source_title": title,
                "verification": "Automatically published: the dated official release parsed to ranks 1-25 of known FBS "
                                "programs and matched CFBD's Playoff Committee Rankings for the same week at every position.",
                "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "canonical_rank_team_sha256": hashlib.sha256(pairs.encode()).hexdigest(),
                "rankings": [{"team": r["team"], "rank": r["rank"], "record": r["record"]} for r in rows],
                "unchanged": ["AP poll", "Coaches poll", "model rankings"]}
    return updated, evidence


def fetch_page(url):
    try:
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; cfb-analytics-verifier)"}), timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def fetch_rankings(key):
    req = Request(f"https://api.collegefootballdata.com/rankings?year={SEASON}&seasonType=regular",
                  headers={"Authorization": f"Bearer {key}", "Accept": "application/json"})
    with urlopen(req, timeout=45) as r:
        return json.load(r)


def run(now, snapshot, known_teams, fetch_page=fetch_page, fetch_rankings=lambda: fetch_rankings(os.environ.get("CFBD_API_KEY", ""))):
    """(updated snapshot, evidence, message); snapshot is None when nothing is published."""
    published = date.fromisoformat(snapshot["cfp_published_at"]) if snapshot.get("cfp_published_at") else None
    day = due_release(now, published)
    if day is None:
        return None, None, "no newer CFP release is due"
    url = official_url(day)
    html = fetch_page(url)
    if html is None:
        return None, None, f"official {day.isoformat()} release not published yet ({url})"
    try:
        rows = parse_official(html, day, known_teams)
        week = verify(rows, cfbd_committee(fetch_rankings()), snapshot.get("cfp_week"))
    except NotPublishable as reason:
        return None, None, f"NOT PUBLISHED: {reason}"
    title = next(iter(re.findall(r"CFP Selection Committee [^|<]*?Rankings of \d{4}", page_text(html))), "CFP Selection Committee Rankings")
    updated, evidence = publish(snapshot, rows, week, day, url, title)
    return updated, evidence, f"published the {day.isoformat()} release (week {week})"


def main():
    snapshot = json.loads(SNAPSHOT.read_text())
    known = {t["team"] for t in json.loads(REPORT.read_text())["rankings"]}
    updated, evidence, message = run(datetime.now(timezone.utc), snapshot, known)
    print(message)
    if message.startswith("NOT PUBLISHED"):
        print(f"::warning::CFP {message}")
    if updated:
        SNAPSHOT.write_text(json.dumps(updated, indent=2) + "\n")
        (EVIDENCE_DIR / f"cfp-publication-{updated['cfp_published_at']}.json").write_text(json.dumps(evidence, indent=1) + "\n")


if __name__ == "__main__":
    main()
