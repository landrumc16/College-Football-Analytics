"""The V6 protected-path guard stays strict except for the reviewed V7 release manifest."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("guard", ROOT / "scripts/verify_protected_changes.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
MANIFEST = json.loads((ROOT / ".github/release-manifests/v7-protected-changes.json").read_text())
V7_ROWS = [("A", "src/cfb_analytics/v7_market_archive.py"), ("A", "web/public/v7-team-lines/texas-tech.json"),
           ("A", "web/public/v7-model-market/texas-tech.json"), ("M", "src/cfb_analytics/refresh.py")]
none_removed = lambda path: 0


def test_manifest_approves_listed_v7_additions_on_v7_branch():
    approved, rejected = guard.evaluate(V7_ROWS, MANIFEST, "v7-development", True, none_removed)
    assert rejected == [] and len(approved) == 4


@pytest.mark.parametrize("head_ref,same_repo", [("main", True), ("beta-rankings-usability", True), ("", True),
                                                ("v7-development", False)])
def test_every_other_branch_and_forks_stay_strict(head_ref, same_repo):
    approved, rejected = guard.evaluate(V7_ROWS, MANIFEST, head_ref, same_repo, none_removed)
    assert approved == [] and len(rejected) == 4


@pytest.mark.parametrize("row", [
    ("M", "src/cfb_analytics/model.py"),                       # existing model code
    ("M", "web/src/scenarios.ts"),                             # released scenario engine (Navigation.tsx: pinned test below)
    ("D", "web/public/v5-program-report-cards.json"),          # deletion
    ("M", "web/public/v7-team-market-history.json"),           # listed as added, not as modified
    ("A", "web/public/v7-team-lines/nested/x.json"),           # outside the pattern
    ("A", "web/public/v7-team-lines/ALL.csv"),                 # bulk download shape
    ("A", "data/v7-raw-lines.json"),                           # unlisted data
    ("A", "web/public/v7-model-market/../season-report.json"),
])
def test_unlisted_or_non_additive_changes_fail_even_on_v7_branch(row):
    _, rejected = guard.evaluate([row], MANIFEST, "v7-development", True, none_removed)
    assert len(rejected) == 1


def test_listed_existing_file_must_be_additive_only():
    _, rejected = guard.evaluate([("M", "src/cfb_analytics/refresh.py")], MANIFEST, "v7-development", True, lambda p: 1)
    assert len(rejected) == 1


def test_missing_manifest_is_strict():
    _, rejected = guard.evaluate(V7_ROWS, None, "v7-development", True, none_removed)
    assert len(rejected) == 4


def test_reviewed_protected_edits_are_pinned_to_exact_content(monkeypatch):
    rows = [("M", "web/src/Navigation.tsx"), ("M", "web/src/EditorialHome.tsx")]
    pinned = {p: MANIFEST["modified_exact"][p]["sha256"] for p, _ in [(r[1], 0) for r in rows]}
    monkeypatch.setattr(guard, "file_sha256", lambda path: pinned[path])
    approved, rejected = guard.evaluate(rows, MANIFEST, "v7-development", True, lambda p: 5)
    assert rejected == [] and len(approved) == 2
    monkeypatch.setattr(guard, "file_sha256", lambda path: "0" * 64)          # any further edit
    _, rejected = guard.evaluate(rows, MANIFEST, "v7-development", True, lambda p: 5)
    assert len(rejected) == 2
    _, rejected = guard.evaluate(rows, MANIFEST, "main", True, lambda p: 5)    # other branches stay strict
    assert len(rejected) == 2
