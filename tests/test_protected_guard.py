"""The V6 protected-path guard is strict on every branch except the reviewed release manifest.

Earlier releases' manifests were removed after merge (the prediction-explanations manifest with this change). The only
manifest now is the temporary, additions-only v7-development event-driven manifest; it must be removed after that merge. The exception mechanism stays tested
with a fixture copy of the reviewed V7 manifest."""
import importlib.util
import os
import subprocess
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


def _manifest(head_ref):
    return next(m for m in guard.load_manifests(MANIFEST_DIR) if m["head_ref"] == head_ref)


def test_reviewed_release_manifests_and_selection_are_per_branch():
    # Temporary v7-development event-driven release manifest (release preparation); remove after that merge.
    # The freshness-reliability manifest is the reviewed exception for that pull request (see the test below).
    manifests = guard.load_manifests(MANIFEST_DIR)
    assert [m["head_ref"] for m in manifests] == ["fix/essential-quota-floor", "freshness-alert-flapping", "freshness-reliability", "fix/game-day-final-detection", "fix/multisource-lifecycle", "fix/shared-acquisition-control", "fix/timely-acquisition", "v7-development", "v9-development"]
    release = next(m for m in manifests if m["head_ref"] == "v7-development")
    assert release["added_file_patterns"] == {} and release["modified_additive_only"] == {} and release["modified_exact"] == {}
    assert guard.select_manifest(manifests, "v7-development", True) is release
    for head_ref, same_repo in (("v8-development", True), ("dual-projection-development", True), ("beta-rankings-usability", True),
                                ("main", True), ("", True), ("prediction-explanations", True), ("v7-development", False),
                                ("freshness-reliability", False), ("freshness-alert-flapping", False)):
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
    listed = set(_manifest("v7-development")["added_files"])
    present = {str(p.relative_to(ROOT)) for p in [*ROOT.glob("src/cfb_analytics/event_*.py"), ROOT / "src/cfb_analytics/cfp_publish.py", ROOT / "src/cfb_analytics/postseason.py"]
               if p.is_file()}
    assert listed == present, {"unlisted": sorted(present - listed), "missing": sorted(listed - present)}


def test_owner_authorized_v9_navigation_matches_exact_scoped_pins(monkeypatch):
    # The V7 fixture above remains unchanged; V9 is a separately authorized interface release.
    m = _manifest("v9-development")
    paths = {"web/src/Navigation.tsx", "web/src/EditorialHome.tsx", "web/src/style.css", "web/public/dual-projections.json", "web/public/prediction-explanations.json"}
    assert set(m["modified_exact"]) == paths
    assert m["added_files"] == m["added_file_patterns"] == m["modified_additive_only"] == {}
    # Published JSON legitimately changes on main's existing data refreshes.
    # Exact live pins are a V9 release-branch gate, not a permanent freeze of production data.
    branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or subprocess.check_output(
        ["git", "branch", "--show-current"], text=True).strip()
    frozen_data_fixture = {}
    for path, entry in m["modified_exact"].items():
        if path.startswith("web/public/") and branch != "v9-development":
            frozen_data_fixture[path] = entry["sha256"]
        else:
            assert guard.head_sha256(path) == entry["sha256"], path
    if frozen_data_fixture:
        actual_hash = guard.file_sha256
        monkeypatch.setattr(guard, "file_sha256", lambda path: frozen_data_fixture.get(path) or actual_hash(path))
    rows = [("M", path) for path in paths]
    approved, rejected = guard.evaluate(rows, m, "v9-development", True, none_removed)
    assert len(approved) == 5 and not rejected
    for branch, same_repo in [("main", True), ("v9-development", False), ("freshness-reliability", True)]:
        approved, rejected = guard.evaluate(rows, m, branch, same_repo, none_removed)
        assert not approved and len(rejected) == 5
    _, rejected = guard.evaluate([("M", "src/cfb_analytics/model.py"), ("M", "web/public/v6-scenario-input.json")],
                                m, "v9-development", True, none_removed)
    assert len(rejected) == 2
    monkeypatch.setattr(guard, "file_sha256", lambda path: "0" * 64)
    approved, rejected = guard.evaluate(rows, m, "v9-development", True, none_removed)
    assert not approved and len(rejected) == 5


def test_freshness_reliability_manifest_is_narrow_and_pins_the_reviewed_content(monkeypatch):
    m = _manifest("freshness-reliability")
    # Archived release fixture: later maintenance legitimately changes these files.
    # The current maintenance manifest below must pin actual committed content instead.
    monkeypatch.setattr(guard, "file_sha256", lambda p: m.get("modified_exact", {}).get(p, {}).get("sha256"))
    assert set(m["added_files"]) == {"src/cfb_analytics/freshness_monitor.py", "src/cfb_analytics/watch_keeper.py"}
    assert m["added_file_patterns"] == {} and m["modified_additive_only"] == {}
    assert set(m["modified_exact"]) == {"src/cfb_analytics/event_watcher.py", "src/cfb_analytics/event_calendar.py",
                                        "src/cfb_analytics/poll_refresh.py"}
    rows = [("A", p) for p in m["added_files"]] + [("M", p) for p in m["modified_exact"]]
    approved, rejected = guard.evaluate(rows, m, "freshness-reliability", True, none_removed)
    assert rejected == [] and len(approved) == 5                     # exactly the reviewed content (SHA-256 pins)
    # No model, data, ratings or published files: anything else is rejected even on this branch.
    _, rejected = guard.evaluate([("M", "src/cfb_analytics/model.py"), ("M", "data/season-2026-report.json"),
                                  ("M", "web/public/sw.js"), ("D", "src/cfb_analytics/cfp_publish.py")],
                                 m, "freshness-reliability", True, none_removed)
    assert len(rejected) == 4


BETA_PATHS = ["src", "data", "research", "web/public", "web/package.json", "web/src/scenarios.ts", "web/src/scenario.worker.ts",
              "web/src/programMetrics.ts", "web/src/Navigation.tsx", "web/src/EditorialHome.tsx", "web/src/style.css",
              "web/src/editorial-polish.css", "web/src/secondary-navigation.css"]


def test_beta_analytics_guard_is_manifest_aware_over_its_full_original_path_list():
    # Owner-authorized (V9): the privacy workflow's visual-identity guard uses the reviewed-manifest mechanism, with
    # the same 13 protected paths as the former strict diff, evaluated on the PR head commit.
    workflow = (ROOT / ".github/workflows/beta-analytics.yml").read_text()
    step = workflow[workflow.index("Preserve the analytics platform and existing visual identity"):workflow.index("mkdir -p web/analytics-evidence")]
    assert "verify_protected_changes.py" in step and '"$CANDIDATE_SHA"' in step and "git diff --exit-code" not in step
    assert step.split("-- ", 1)[1].split(")")[0].split() == BETA_PATHS


def test_v9_exception_covers_only_pinned_files_and_unauthorized_changes_still_fail(monkeypatch):
    m = _manifest("v9-development")
    pinned = {p: e["sha256"] for p, e in m["modified_exact"].items()}
    monkeypatch.setattr(guard, "file_sha256", lambda path: pinned.get(path, "f" * 64))
    approved, rejected = guard.evaluate([("M", p) for p in pinned], m, "v9-development", True, none_removed)
    assert len(approved) == len(pinned) == 5 and not rejected
    # Anything else in the beta path list, a different style.css, a deletion, or another branch is rejected.
    unauthorized = [("M", "web/src/editorial-polish.css"), ("M", "web/src/secondary-navigation.css"), ("M", "src/cfb_analytics/model.py"),
                    ("M", "data/season-2026-report.json"), ("D", "web/src/style.css"), ("A", "web/public/new-data.json")]
    _, rejected = guard.evaluate(unauthorized, m, "v9-development", True, none_removed)
    assert len(rejected) == len(unauthorized)
    monkeypatch.setattr(guard, "file_sha256", lambda path: "0" * 64)      # style.css edited after review
    _, rejected = guard.evaluate([("M", "web/src/style.css")], m, "v9-development", True, none_removed)
    assert len(rejected) == 1
    for branch, same_repo in (("main", True), ("public-beta-analytics", True), ("v9-development", False)):
        _, rejected = guard.evaluate([("M", "web/src/style.css")], m, branch, same_repo, none_removed)
        assert len(rejected) == 1


def test_freshness_alert_flapping_manifest_pins_only_the_monitor(monkeypatch):
    m = _manifest("freshness-alert-flapping")
    monkeypatch.setattr(guard, "file_sha256", lambda p: m.get("modified_exact", {}).get(p, {}).get("sha256"))
    assert m["added_files"] == {} and m["added_file_patterns"] == {} and m["modified_additive_only"] == {}
    assert set(m["modified_exact"]) == {"src/cfb_analytics/freshness_monitor.py"}
    approved, rejected = guard.evaluate([("M", "src/cfb_analytics/freshness_monitor.py")], m, "freshness-alert-flapping", True, none_removed)
    assert rejected == [] and len(approved) == 1
    _, rejected = guard.evaluate([("M", "src/cfb_analytics/event_watcher.py"), ("M", "data/season-2026-report.json")],
                                 m, "freshness-alert-flapping", True, none_removed)
    assert len(rejected) == 2


def test_game_day_final_detection_pins_current_content_and_preserves_rejection(monkeypatch):
    m = _manifest("fix/game-day-final-detection")
    # Released fixture; current maintenance is pinned by its own manifest below.
    monkeypatch.setattr(guard, "file_sha256", lambda p: m.get("modified_exact", {}).get(p, {}).get("sha256"))
    paths = {"src/cfb_analytics/event_watcher.py", "src/cfb_analytics/freshness_monitor.py",
             ".github/workflows/refresh-data.yml"}
    assert set(m["modified_exact"]) == paths
    assert not m["added_files"] and not m["modified_additive_only"] and not m["added_file_patterns"]
    rows = [("M", p) for p in paths]
    approved, rejected = guard.evaluate(rows, m, m["head_ref"], True, none_removed)
    assert len(approved) == 3 and not rejected
    for branch, same_repo in [("main", True), (m["head_ref"], False), ("v9-development", True)]:
        assert len(guard.evaluate(rows, m, branch, same_repo, none_removed)[1]) == 3
    unauthorized = [("M", "src/cfb_analytics/model.py"), ("M", "data/season-2026-report.json"),
                    ("D", "src/cfb_analytics/event_watcher.py")]
    assert len(guard.evaluate(unauthorized, m, m["head_ref"], True, none_removed)[1]) == 3
    monkeypatch.setattr(guard, "file_sha256", lambda p: "0" * 64)
    assert len(guard.evaluate(rows, m, m["head_ref"], True, none_removed)[1]) == 3


def test_shared_acquisition_manifest_pins_only_reviewed_transport_and_workflows(monkeypatch):
    m = _manifest('fix/shared-acquisition-control')
    # Released fixture; the PR #80 quota-floor correction is pinned by its own manifest below.
    monkeypatch.setattr(guard, 'file_sha256', lambda p: m.get('modified_exact', {}).get(p, {}).get('sha256'))
    assert set(m['added_files']) == {'src/cfb_analytics/quota_client.py'}
    assert not m['added_file_patterns'] and not m['modified_additive_only']
    rows = [('A', p) for p in m['added_files']] + [('M', p) for p in m['modified_exact']]
    assert not guard.evaluate(rows, m, m['head_ref'], True, none_removed)[1]
    assert len(guard.evaluate(rows, m, 'main', True, none_removed)[1]) == len(rows)
    assert len(guard.evaluate(rows, m, m['head_ref'], False, none_removed)[1]) == len(rows)
    monkeypatch.setattr(guard, 'file_sha256', lambda p: '0' * 64)
    assert len(guard.evaluate([('M', p) for p in m['modified_exact']], m, m['head_ref'], True, none_removed)[1]) == len(m['modified_exact'])


def test_timely_acquisition_manifest_is_narrow(monkeypatch):
    m = _manifest('fix/timely-acquisition')
    rows = [('M', 'src/cfb_analytics/v8_sources.py')]
    assert len(m['modified_exact']) == 1
    assert not guard.evaluate(rows, m, m['head_ref'], True, none_removed)[1]
    assert guard.evaluate(rows, m, 'main', True, none_removed)[1]
    assert guard.evaluate(rows, m, m['head_ref'], False, none_removed)[1]
    monkeypatch.setattr(guard, 'file_sha256', lambda p: '0' * 64)
    assert guard.evaluate(rows, m, m['head_ref'], True, none_removed)[1]


def test_multisource_manifest_rejects_drift_and_other_branches(monkeypatch):
    m = _manifest('fix/multisource-lifecycle')
    rows = [('A', p) for p in m['added_files']] + [('M', p) for p in m['modified_exact']]
    assert not guard.evaluate(rows, m, m['head_ref'], True, none_removed)[1]
    assert len(guard.evaluate(rows, m, 'main', True, none_removed)[1]) == len(rows)
    assert len(guard.evaluate(rows, m, m['head_ref'], False, none_removed)[1]) == len(rows)
    monkeypatch.setattr(guard, 'file_sha256', lambda p: '0' * 64)
    assert guard.evaluate([('M', p) for p in m['modified_exact']], m, m['head_ref'], True, none_removed)[1]


def test_essential_quota_floor_manifest_pins_only_the_quota_correction(monkeypatch):
    m = _manifest('fix/essential-quota-floor')
    assert set(m['modified_exact']) == {'src/cfb_analytics/quota_client.py', '.github/workflows/refresh-data.yml'}
    assert not m['added_files'] and not m['added_file_patterns'] and not m['modified_additive_only']
    rows = [('M', p) for p in m['modified_exact']]
    # Released fixture: this branch later merged PR #80, so its content is pinned by the multisource manifest.
    monkeypatch.setattr(guard, 'file_sha256', lambda p: m['modified_exact'][p]['sha256'])
    assert not guard.evaluate(rows, m, m['head_ref'], True, none_removed)[1]
    for branch, same_repo in (('main', True), (m['head_ref'], False)):
        assert len(guard.evaluate(rows, m, branch, same_repo, none_removed)[1]) == 2
    others = [('M', 'src/cfb_analytics/event_watcher.py'), ('M', 'src/cfb_analytics/model.py'), ('D', 'src/cfb_analytics/quota_client.py')]
    assert len(guard.evaluate(others, m, m['head_ref'], True, none_removed)[1]) == 3
    monkeypatch.setattr(guard, 'file_sha256', lambda p: '0' * 64)                # any later edit fails
    assert len(guard.evaluate(rows, m, m['head_ref'], True, none_removed)[1]) == 2
