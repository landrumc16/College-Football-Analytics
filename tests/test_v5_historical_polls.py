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
                                            "poll", "team_id", "rank",\n                                            "prev_rank", "weeks_ranked"])
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
        rows[-1]["rank"] = 23  # invalid: duplicates No. 23 while No. 24 remains
    else:
        rows[-1]["team_id"] = rows[-2]["team_id"]
    with pytest.raises(ValueError):
        extract_snapshots(encode(rows), 2024)


def test_rejects_wrong_season():
    with pytest.raises(ValueError):
        extract_snapshots(encode(source_rows(2023)), 2024)


def test_genuine_tied_poll_positions_are_preserved():
    rows = source_rows()
    # A tied No. 14 produces positions 14, 14, 16 (not a duplicate error).
    ap_final = [row for row in rows if row['poll'] == 'ap' and row['season_type'] == 3]
    ap_final[14]['rank'] = 14
    result = extract_snapshots(encode(rows), 2024)
    ranks = [entry['rank'] for entry in result['snapshots']['ap_final']]
    assert ranks.count(14) == 2 and 15 not in ranks and 16 in ranks


def test_invalid_duplicate_rank_without_competition_gap_is_rejected():
    rows = source_rows()
    ap_final = [row for row in rows if row['poll'] == 'ap' and row['season_type'] == 3]
    ap_final[14]['rank'] = 14
    ap_final[15]['rank'] = 15  # still invalid: competition rank must skip 15
    with pytest.raises(ValueError):
        extract_snapshots(encode(rows), 2024)


def test_2025_week_two_unranked_prior_week_candidate_is_research_only():
    rows = source_rows(2025)
    for row in rows:
        row["prev_rank"] = ""
        row["weeks_ranked"] = "1"
        if row["season_type"] == 2:
            row["week"] = 2
    result = extract_snapshots(encode(rows), 2025)
    assert result["source_weeks"]["ap_preseason"] == 2
    assert result["source_weeks"]["coaches_preseason"] == 2
    assert result["source_weeks"]["ap_final"] == 1


def test_2025_week_two_with_prior_rank_is_not_misclassified_as_preseason():
    rows = source_rows(2025)
    for row in rows:
        row["prev_rank"] = ""
        row["weeks_ranked"] = "1"
        if row["season_type"] == 2:
            row["week"] = 2
    rows[0]["prev_rank"] = "1"
    with pytest.raises(ValueError, match="2025 ap preseason"):
        extract_snapshots(encode(rows), 2025)
