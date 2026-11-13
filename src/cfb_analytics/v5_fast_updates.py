"""Fail-closed reconciliation for fast college football score and poll feeds.

A single source can be shown provisionally. Only independent matching
observations become confirmed and eligible for downstream model ingestion.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit

KINDS = {"game_final", "ap_top25", "coaches_top25", "cfp_top25"}


def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Missing publication timestamp")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timestamp must include timezone")
    if dt > datetime.now(timezone.utc):
        raise ValueError("Future publication timestamp")
    return dt


def _payload(record):
    kind = record["kind"]
    if kind not in KINDS:
        raise ValueError("Unsupported update kind")
    if kind == "game_final":
        if record.get("status") != "final":
            raise ValueError("Only final game scores may be reconciled")
        teams = (record.get("home"), record.get("away"))
        if any(not isinstance(t, str) or not t.strip() for t in teams) or teams[0] == teams[1]:
            raise ValueError("Invalid game teams")
        scores = (record.get("home_score"), record.get("away_score"))
        if any(type(n) is not int or n < 0 for n in scores):
            raise ValueError("Invalid final score")
        if not str(record.get("game_id", "")).strip():
            raise ValueError("Missing stable game ID")
        return (str(record["game_id"]), *teams, *scores)
    rows = record.get("rankings")
    if not isinstance(rows, list) or len(rows) != 25:
        raise ValueError("Poll requires complete Top 25")
    if any(type(row.get("rank")) is not int or not 1 <= row["rank"] <= 25 or
           not isinstance(row.get("team"), str) or not row["team"].strip() for row in rows):
        raise ValueError("Invalid ranking")
    if {row["rank"] for row in rows} != set(range(1, 26)) or len({row["team"] for row in rows}) != 25:
        raise ValueError("Duplicate rank or team")
    if type(record.get("season")) is not int or type(record.get("week")) is not int:
        raise ValueError("Missing poll season/week")
    return (record["season"], record["week"],
            tuple(sorted((row["rank"], row["team"]) for row in rows)))


def _provider(source):
    """Group URLs by upstream publisher, not merely by API hostname."""
    host = (urlsplit(source).hostname or "").lower().rstrip(".")
    if host == "espn.com" or host.endswith(".espn.com"):
        return "espn"
    if host == "ncaa.org" or host.endswith(".ncaa.org"):
        return "ncaa"
    if host == "collegefootballdata.com" or host.endswith(".collegefootballdata.com"):
        return "collegefootballdata"
    # Unknown domains are conservative: subdomains do not count separately.
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def reconcile(observations):
    """Return safe public snapshot; confirmed payload only after two independent sources.

    An unconfirmed new payload never overwrites the most recent confirmed
    record. Caller persists and serves confirmed records separately.
    """
    if not observations:
        raise ValueError("No observations")
    candidates = {}
    for row in observations:
        if not isinstance(row.get("source"), str) or not row["source"].startswith("https://") or not urlsplit(row["source"]).hostname:
            raise ValueError("Missing source URL")
        _timestamp(row.get("published_at"))
        key = (row["kind"], _payload(row))
        candidates.setdefault(key, []).append(row)
    if len({kind for kind, _ in candidates}) != 1:
        raise ValueError("Cannot reconcile mixed update kinds")
    # Never reconcile different games or poll editions in one publication.
    identities = set()
    for kind, payload in candidates:
        identities.add((kind, payload[0]) if kind == "game_final" else (kind, payload[0], payload[1]))
    if len(identities) != 1:
        raise ValueError("Cannot reconcile different games or poll editions")
    # A provider host must not attest to incompatible payloads, even through
    # multiple URLs. Such evidence is disputed, not independent confirmation.
    host_payloads = {}
    for (_, payload), rows in candidates.items():
        for row in rows:
            host = _provider(row["source"])
            if host in host_payloads and host_payloads[host] != payload:
                return {"status": "disputed", "kind": observations[0]["kind"],
                        "data": None, "sources": sorted({r["source"] for r in observations})}
            host_payloads[host] = payload
    confirmed = []
    for (kind, payload), rows in candidates.items():
        sources = {r["source"] for r in rows}
        independent_hosts = {_provider(source) for source in sources}
        if len(independent_hosts) >= 2:
            confirmed.append((max(_timestamp(r["published_at"]) for r in rows), kind, payload, rows))
    if len(confirmed) > 1:
        raise ValueError("Conflicting independently confirmed payloads")
    if confirmed and len(candidates) > 1:
        return {"status": "disputed", "kind": observations[0]["kind"],
                "data": None, "sources": sorted({r["source"] for r in observations})}
    if confirmed:
        _, kind, payload, rows = confirmed[0]
        return {"status": "confirmed", "kind": kind, "data": rows[0],
                "sources": sorted({r["source"] for r in rows})}
    # A disagreement is not silently resolved by choosing whichever arrived last.
    if len(candidates) != 1:
        return {"status": "disputed", "kind": observations[0]["kind"],
                "data": None, "sources": sorted({r["source"] for r in observations})}
    row = observations[0]
    return {"status": "provisional", "kind": row["kind"], "data": row,
            "sources": sorted({r["source"] for r in observations})}
