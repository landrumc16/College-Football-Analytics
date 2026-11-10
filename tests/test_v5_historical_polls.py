import csv
import io

import pytest

from scripts.fetch_v5_historical_polls import extract_snapshots


def source_rows(year=2024):
    rows = []
    for poll in ("ap", "coaches"):
        for season_type in (2, 3):
            for rank in range(1, 26):
                rows.append(dict(season=year, season_type=season_type, week=1,
                                 poll=poll, team_id=rank + (100 if poll == "coaches" else 0),
                                 rank=rank))
    return rows


def encode(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["season", "season_type", "week",
                                            "poll", "team_id", "rank"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode()


def test_all_four_snapshots_and_provenance():
    result = extract_snapshots(encode(source_rows()), 2024)
    assert len(result["snapshots"]) == 4
    assert all(len(rows) == 25 for rows in result["snapshots"].values())
    assert len(result["source_sha256"]) == 64


def test_null_exit_rows_not_counted():
    rows = source_rows()
    rows.append(dict(season=2024, season_type=2, week=1, poll="ap",
                     team_id=999, rank=""))
    assert len(extract_snapshots(encode(rows), 2024)["snapshots"]["ap_preseason"]) == 25


@pytest.mark.parametrize("mutation", ["missing", "duplicate_rank", "duplicate_team"])
def test_refuses_incomplete_or_corrupt_snapshots(mutation):
    rows = source_rows()
    if mutation == "missing":
        rows.pop()
    elif mutation == "duplicate_rank":
        rows[-1]["rank"] = 24
    else:
        rows[-1]["team_id"] = rows[-2]["team_id"]
    with pytest.raises(ValueError):
        extract_snapshots(encode(rows), 2024)


def test_rejects_wrong_season():
    with pytest.raises(ValueError):
        extract_snapshots(encode(source_rows(2023)), 2024)
