"""The V6 protected-path guard is strict on every branch except the reviewed release manifest.

Earlier releases' manifests were removed after merge (the prediction-explanations manifest with this change). The only
manifest now is the temporary, additions-only v7-development event-driven manifest; it must be removed after that merge. The exception mechanism stays tested
with a fixture copy of the reviewed V7 manifest."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("guard", ROOT / "scripts/verify_protected_changes.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
MANIFEST_DIR = ROOT / ".github/release-manifests"
# Fixture: the reviewed V7 manifest as it was approved (removed from the repository after release).
MANIFEST = {
    "head_ref": "v7-development",
    "added_files": {"src/cfb_analytics/v7_market_archive.py": "reviewed V7 change (fixture)", "src/cfb_analytics/v7_market_metrics.py": "reviewed V7 change (fixture)",
                    "src/cfb_analytics/v7_validation.py": "reviewed V7 change (fixture)", "data/v7-market-receipts.json": "reviewed V7 change (fixture)",
                    "research/v7/historical-validation.json": "reviewed V7 change (fixture)", "web/public/v7-team-market-history.json": "reviewed V7 change (fixture)",
                    "web/public/v7-market-metrics.json": "reviewed V7 change (fixture)"},
    "added_file_patterns": {"web/public/v7-team-lines/": "reviewed V7 change (fixture)", "web/public/v7-model-market/": "reviewed V7 change (fixture)"},
    "modified_additive_only": {"src/cfb_analytics/refresh.py": "reviewed V7 change (fixture)"},
    "modified_exact": {
        "web/src/Navigation.tsx": {"sha256": "8aa30905d3278b171123af2e4fb683660d18cb34e6a609d4bb258654a044991a",
                                   "reason": "V7 navigation (fixture)"},
        "web/src/EditorialHome.tsx": {"sha256": "7d212f3b00d91450abb4aa3deca088300fd0f7cce6f86424a80c54b78db59daf",
                                      "reason": "V7 bottom navigation (fixture)"},
    },
}
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


def test_only_the_additions_only_event_driven_manifest_remains_and_selection_is_per_branch():
    # Temporary v7-development event-driven release manifest (release preparation); remove after that merge.
    manifests = guard.load_manifests(MANIFEST_DIR)
    assert [m["head_ref"] for m in manifests] == ["v7-development"]
    release = manifests[0]
    assert release["added_file_patterns"] == {} and release["modified_additive_only"] == {} and release["modified_exact"] == {}
    assert guard.select_manifest(manifests, "v7-development", True) is release
    for head_ref, same_repo in (("v8-development", True), ("dual-projection-development", True), ("beta-rankings-usability", True),
                                ("main", True), ("", True), ("prediction-explanations", True), ("v7-development", False)):
        assert guard.select_manifest(manifests, head_ref, same_repo) is None
        _, rejected = guard.evaluate(V7_ROWS + [("M", "web/src/Navigation.tsx")], None, head_ref, same_repo,
                                     none_removed)
        assert len(rejected) == 5
    # Additions only: any modification or deletion of an existing protected file is still rejected.
    _, rejected = guard.evaluate([("M", "web/src/Navigation.tsx"), ("M", "src/cfb_analytics/dual_publish.py"),
                                  ("D", "web/public/dual-projections.json"), ("M", "src/cfb_analytics/event_watcher.py")],
                                 release, "v7-development", True, none_removed)
    assert len(rejected) == 4


def test_event_driven_manifest_lists_exactly_the_new_protected_files():
    listed = set(guard.load_manifests(MANIFEST_DIR)[0]["added_files"])
    present = {str(p.relative_to(ROOT)) for p in [*ROOT.glob("src/cfb_analytics/event_*.py"), ROOT / "src/cfb_analytics/cfp_publish.py", ROOT / "src/cfb_analytics/postseason.py"]
               if p.is_file()}
    assert listed == present, {"unlisted": sorted(present - listed), "missing": sorted(listed - present)}


def test_released_v7_navigation_matches_the_reviewed_pins():
    # Production still carries exactly the owner-reviewed V7 navigation; any future edit needs a new review.
    for path, entry in MANIFEST["modified_exact"].items():
        assert guard.head_sha256(path) == entry["sha256"], path
