"""Exercise the actual publication script against local bare Git remotes (no APIs)."""
import json
from pathlib import Path
import subprocess
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/publish_refresh_snapshot.sh"


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=check)


def write(repo, name, value):
    (repo / name).write_text(json.dumps(value) + "\n")
    git(repo, "add", name)


@pytest.fixture
def repos(tmp_path):
    remote, writer, refresh = (tmp_path / p for p in ("remote.git", "writer", "refresh"))
    subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(remote)], check=True, capture_output=True)
    for repo in (writer, refresh):
        subprocess.run(["git", "clone", str(remote), str(repo)], check=True, capture_output=True)
        git(repo, "config", "user.name", "Test")
        git(repo, "config", "user.email", "test@example.invalid")
    write(writer, "snapshot.json", {"completed": False})
    write(writer, "pregame.json", {"retained_before_kickoff": True})
    git(writer, "commit", "-m", "Initial retained data")
    git(writer, "push", "origin", "main")
    git(refresh, "pull", "origin", "main")
    return remote, writer, refresh


def publish(repo):
    return subprocess.run(["bash", str(SCRIPT)], cwd=repo, text=True, capture_output=True)


def test_non_conflicting_newer_production_change_and_pregame_archive_survive(repos):
    remote, writer, refresh = repos
    before = (refresh / "pregame.json").read_bytes()
    write(refresh, "snapshot.json", {"completed": True, "score": [48, 27]})
    write(writer, "reliability.json", {"newer_fix": True})
    git(writer, "commit", "-m", "Independent newer production fix")
    git(writer, "push", "origin", "main")
    assert publish(refresh).returncode == 0
    git(writer, "pull", "--ff-only", "origin", "main")
    assert json.loads((writer / "snapshot.json").read_text())["score"] == [48, 27]
    assert json.loads((writer / "reliability.json").read_text())["newer_fix"]
    assert (writer / "pregame.json").read_bytes() == before


def test_conflict_never_pushes_or_leaves_merge_markers_and_fresh_retry_succeeds(repos):
    remote, writer, refresh = repos
    write(refresh, "snapshot.json", {"completed": True, "revision": "stale-refresh"})
    write(writer, "snapshot.json", {"completed": True, "revision": "newer-production"})
    git(writer, "commit", "-m", "Newer independently verified source")
    git(writer, "push", "origin", "main")
    head = git(writer, "rev-parse", "HEAD").stdout
    result = publish(refresh)
    assert result.returncode != 0 and "no push performed" in result.stderr
    assert git(remote, "rev-parse", "main").stdout == head
    assert not (refresh / ".git/rebase-merge").exists()
    assert json.loads((refresh / "snapshot.json").read_text())["revision"] == "stale-refresh"
    # A new runner starts from current main and regenerates data, exactly as the recovery run does.
    retry = refresh.parent / "retry"
    subprocess.run(["git", "clone", str(remote), str(retry)], check=True, capture_output=True)
    git(retry, "config", "user.name", "Test")
    git(retry, "config", "user.email", "test@example.invalid")
    write(retry, "snapshot.json", {"completed": True, "revision": "fresh-revalidated"})
    assert publish(retry).returncode == 0
    git(writer, "pull", "--ff-only", "origin", "main")
    assert json.loads((writer / "snapshot.json").read_text())["revision"] == "fresh-revalidated"


def test_no_changes_does_not_create_or_push_a_commit(repos):
    remote, writer, refresh = repos
    head = git(remote, "rev-parse", "main").stdout
    assert publish(refresh).returncode == 0
    assert git(remote, "rev-parse", "main").stdout == head


def test_newer_archive_entry_cannot_be_replaced_by_a_refresh(repos):
    remote, writer, refresh = repos
    write(refresh, "first-observation.json", {"issued": "later-candidate"})
    write(writer, "first-observation.json", {"issued": "earlier-authentic"})
    git(writer, "commit", "-m", "First authentic retained observation")
    git(writer, "push", "origin", "main")
    head = git(remote, "rev-parse", "main").stdout
    assert publish(refresh).returncode != 0
    assert git(remote, "rev-parse", "main").stdout == head
    assert json.loads((writer / "first-observation.json").read_text())["issued"] == "earlier-authentic"


def test_refresh_workflow_uses_current_branch_and_tested_publication_script():
    workflow = (SCRIPT.parents[1] / ".github/workflows/refresh-data.yml").read_text()
    assert workflow.count("ref: ${{ github.ref }}") == 2
    assert "bash scripts/publish_refresh_snapshot.sh" in workflow
