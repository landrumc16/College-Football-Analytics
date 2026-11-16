"""V6 protected-path guard: strict everywhere except the owner-approved, SHA-256-pinned PR #34 manifest."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("guard", ROOT / "scripts/verify_protected_changes.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
MANIFEST = json.loads((ROOT / ".github/release-manifests/rankings-beta-protected-changes.json").read_text())
NAV = ("M", "web/src/Navigation.tsx")
PIN = MANIFEST["modified_exact"]["web/src/Navigation.tsx"]["sha256"]


def run(rows, head_ref="beta-rankings-usability", same_repo=True, content=PIN, monkeypatch=None):
    monkeypatch.setattr(guard, "file_sha256", lambda path: content)
    manifest = guard.select_manifest([MANIFEST], head_ref, same_repo)
    return guard.evaluate(rows, manifest, head_ref, same_repo, lambda p: 1)


def test_exact_reviewed_navigation_is_approved_only_for_pr34_branch(monkeypatch):
    approved, rejected = run([NAV], monkeypatch=monkeypatch)
    assert rejected == [] and len(approved) == 1


def test_committed_navigation_matches_the_pin():
    assert guard.head_sha256("web/src/Navigation.tsx") == PIN


@pytest.mark.parametrize("head_ref,same_repo", [("main", True), ("v7-development", True), ("", True),
                                                ("beta-rankings-usability", False)])
def test_other_branches_forks_and_pushes_stay_strict(monkeypatch, head_ref, same_repo):
    _, rejected = run([NAV], head_ref=head_ref, same_repo=same_repo, monkeypatch=monkeypatch)
    assert len(rejected) == 1


def test_any_further_navigation_edit_fails(monkeypatch):
    _, rejected = run([NAV], content="0" * 64, monkeypatch=monkeypatch)
    assert len(rejected) == 1


@pytest.mark.parametrize("row", [("M", "web/src/EditorialHome.tsx"), ("M", "web/src/scenarios.ts"),
                                 ("M", "web/public/v5-program-report-cards.json"), ("D", "web/src/Navigation.tsx"),
                                 ("A", "web/public/new.json"), ("M", "src/cfb_analytics/model.py")])
def test_unrelated_protected_changes_fail_on_pr34_branch(monkeypatch, row):
    _, rejected = run([row], monkeypatch=monkeypatch)
    assert len(rejected) == 1


def test_manifest_selection_is_unique_per_branch():
    assert guard.select_manifest([], "beta-rankings-usability", True) is None
    with pytest.raises(SystemExit):
        guard.select_manifest([MANIFEST, MANIFEST], "beta-rankings-usability", True)
