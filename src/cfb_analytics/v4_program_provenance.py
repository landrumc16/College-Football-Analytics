"""Strict provenance gate for published historical program intelligence.

A descriptive ranking is only as trustworthy as its source records. This gate
requires independently attributable season-specific source references and
prevents publishing an empty or incomplete historical dataset as authoritative.
"""
from __future__ import annotations

from collections import defaultdict
from urllib.parse import urlparse


def validate_program_sources(strength_rows: list[dict], poll_rows: list[dict],
                             latest_season: int, expected_seasons: int = 10) -> dict:
    if not isinstance(latest_season, int) or isinstance(latest_season, bool):
        raise ValueError("Invalid latest season")
    if not isinstance(expected_seasons, int) or isinstance(expected_seasons, bool) or expected_seasons < 3:
        raise ValueError("Invalid expected seasons")
    earliest = latest_season - expected_seasons + 1
    coverage = defaultdict(set)
    poll_coverage = defaultdict(set)
    observed = set()
    for kind, rows in (("strength", strength_rows), ("poll", poll_rows)):
        for row in rows:
            season = row.get("season")
            source = row.get("source")
            if not isinstance(season, int) or isinstance(season, bool) or not earliest <= season <= latest_season:
                raise ValueError(f"{kind}: season outside completed window")
            if not isinstance(source, str) or not source.strip():
                raise ValueError(f"{kind}: missing source")
            if source.startswith(("http://", "https://")):
                parsed = urlparse(source)
                if not parsed.netloc:
                    raise ValueError(f"{kind}: invalid source URL")
            elif not source.startswith("sha256:") or len(source) != 71 or any(
                ch not in "0123456789abcdef" for ch in source[7:]
            ):
                raise ValueError(f"{kind}: source must be URL or sha256 digest")
            team = row.get("team")
            if not isinstance(team, str) or not team.strip():
                raise ValueError(f"{kind}: missing team")
            identity = (kind, team, season, row.get("poll") if kind == "poll" else None)
            if identity in observed:
                raise ValueError(f"{kind}: duplicate team-season observation")
            observed.add(identity)
            if kind == "strength":
                coverage[team].add(season)
            else:
                poll = row.get("poll")
                if poll not in ("AP", "Coaches"):
                    raise ValueError("Unknown poll")
                poll_coverage[(team, poll)].add(season)
    return {
        "status": "provenance_format_checked_not_independently_verified",
        "required_window": [earliest, latest_season],
        "strength_programs_full_window": sum(len(years) == expected_seasons for years in coverage.values()),
        "strength_programs_partial": sum(len(years) < expected_seasons for years in coverage.values()),
        "poll_programs_full_window": sum(len(years) == expected_seasons for years in poll_coverage.values()),
        "source_authenticity_verified": False,
        "historical_rankings_ready": False,
        "note": "Format and coverage checks do not establish source authenticity or opponent-adjusted comparability.",
    }
