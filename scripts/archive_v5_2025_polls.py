"""Build permanent 2025 poll research snapshot from independently sourced preseason
rankings and source-extracted final rankings. Never silently reuse week-2 polls.
"""
import json
from pathlib import Path

from scripts.fetch_v5_historical_polls import BASE, extract_snapshots, fetch_source, valid_top25


def build_2025(root: Path, curated_path: Path, identity_path: Path) -> dict:
    curated = json.loads(curated_path.read_text())
    identities = json.loads(identity_path.read_text())["mapping"]
    reverse = {name: team_id for team_id, name in identities.items()}
    if len(reverse) != len(identities):
        raise ValueError("Duplicate canonical program names")
    if curated["season"] != 2025:
        raise ValueError("Wrong curated preseason season")
    # Read raw 2025 feed only for postseason rankings. Its preseason field is
    # known invalid and MUST NOT pass extract_snapshots().
    import csv
    import hashlib
    from io import StringIO
    raw = fetch_source(BASE.format(year=2025))
    rows = list(csv.DictReader(StringIO(raw.decode("utf-8-sig"))))
    snapshots = {}
    for poll in ("ap", "coaches"):
        preseason = curated["polls"][poll]
        if len(preseason["source_urls"]) < 2:
            raise ValueError("Preseason requires two independently documented sources")
        pairs = []
        for row in preseason["teams"]:
            if row["team"] not in reverse:
                raise ValueError(f"Unmapped 2025 preseason team: {row['team']}")
            pairs.append({"team_id": reverse[row["team"]], "rank": row["rank"]})
        if not valid_top25([p["rank"] for p in pairs], [p["team_id"] for p in pairs]):
            raise ValueError(f"Invalid curated {poll} preseason")
        snapshots[f"{poll}_preseason"] = sorted(pairs, key=lambda p: (p["rank"], p["team_id"]))
        final = [
            {"team_id": str(row["team_id"]), "rank": int(row["rank"])}
            for row in rows if int(row["season"]) == 2025
            and int(row["season_type"]) == 3 and int(row["week"]) == 1
            and row["poll"].lower() == poll and row["rank"] not in ("", "null", "NA")
        ]
        if not valid_top25([p["rank"] for p in final], [p["team_id"] for p in final]):
            raise ValueError(f"Invalid {poll} final poll")
        if set(p["team_id"] for p in final) - set(identities):
            raise ValueError(f"Unmapped {poll} final poll teams")
        snapshots[f"{poll}_final"] = sorted(final, key=lambda p: (p["rank"], p["team_id"]))
    data = {
        "season": 2025,
        "status": "research_only_requires_independent_final_poll_review",
        "publishable": False,
        "source_review_attested": False,
        "source_url": BASE.format(year=2025),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_weeks": {"ap_preseason": None, "coaches_preseason": None,
                         "ap_final": 1, "coaches_final": 1},
        "preseason_provenance": {
            poll: {"date": curated["polls"][poll]["date"],
                   "source_urls": curated["polls"][poll]["source_urls"]}
            for poll in ("ap", "coaches")
        },
        "snapshots": snapshots,
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "poll-snapshots-2025.json").write_text(json.dumps(data, indent=2) + "\n")
    return data


if __name__ == "__main__":
    build_2025(
        Path("research/archive/polls"),
        Path("research/v5-2025-preseason-polls-verified.json"),
        Path("research/v5-national-identity-candidates.json"),
    )
