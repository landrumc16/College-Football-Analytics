import csv
import gzip
import hashlib
import json
from unittest.mock import patch

import pytest

from cfb_analytics.v5_ncaa_schedule_acquire import acquire, BASE


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def test_acquire_retains_original_bytes_hash_columns_and_unverified_status(tmp_path):
    data = "contest_id,team_id,opponent_id\n100,1,2\n"
    compressed = gzip.compress(data.encode())
    urls = []

    def download(url, timeout):
        urls.append(url)
        return FakeResponse(compressed)

    with patch("cfb_analytics.v5_ncaa_schedule_acquire.urlopen", side_effect=download):
        inventory = acquire(tmp_path, first=2024, last=2025)

    assert urls == [BASE.replace("ncaa_mfb_schedule/", f"ncaa_mfb_{dataset}/") + f"ncaa_mfb_{dataset}_{year}.csv.gz"
                    for year in (2024, 2025) for dataset in ("schedule", "teams", "linescore")]
    assert inventory["status"] == "raw_ncaa_origin_not_yet_reconciled"
    assert len(inventory["seasons"]) == 6
    assert inventory["seasons"][0]["sha256"] == hashlib.sha256(compressed).hexdigest()
    assert inventory["seasons"][0]["columns"] == ["contest_id", "team_id", "opponent_id"]
    assert (tmp_path / "ncaa_mfb_schedule_2024.csv.gz").read_bytes() == compressed
    assert json.loads((tmp_path / "inventory.json").read_text()) == inventory


@pytest.mark.parametrize("first,last", [(2012, 2016), (2024, 2026), (2025, 2024)])
def test_acquire_rejects_out_of_range_years(tmp_path, first, last):
    with pytest.raises(ValueError):
        acquire(tmp_path, first=first, last=last)


def test_acquire_rejects_empty_dataset(tmp_path):
    compressed = gzip.compress(b"contest_id,team_id\n")
    with patch("cfb_analytics.v5_ncaa_schedule_acquire.urlopen",
               return_value=FakeResponse(compressed)):
        with pytest.raises(ValueError, match="No NCAA schedule rows"):
            acquire(tmp_path, first=2024, last=2024)
