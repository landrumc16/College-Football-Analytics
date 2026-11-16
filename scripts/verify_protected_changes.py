"""V6 protected-path guard with a narrowly scoped, reviewed release manifest.

Default (any branch): protected paths must be byte-identical to the merge base, exactly as before.
Only a same-repository pull request whose head branch equals the manifest's head_ref may carry the
manifest's explicitly listed additions, and additive-only edits to the listed existing files.
Reviewed edits to protected files are pinned by the exact SHA-256 of their committed content ("modified_exact"):
any further change to such a file fails until the manifest is re-reviewed.
Deletions, renames, mode changes and any other modification still fail.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

MANIFEST = Path(".github/release-manifests/v7-protected-changes.json")
SLUG_JSON = re.compile(r"^[a-z0-9-]+\.json$")


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


def changes(base, paths):
    rows = []
    for line in git("diff", "--name-status", "--no-renames", base, "HEAD", "--", *paths).splitlines():
        status, path = line.split("\t", 1)
        rows.append((status, path))
    return rows


def deletions(base, path):
    added, removed, _ = git("diff", "--numstat", base, "HEAD", "--", path).split("\t", 2)
    return int(removed)


def head_sha256(path):
    return hashlib.sha256(subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, check=True).stdout).hexdigest()


file_sha256 = head_sha256


def evaluate(rows, manifest, head_ref, same_repo, removed_lines):
    """Return (approved, rejected) lists. removed_lines(path) -> lines deleted versus the base."""
    applies = manifest is not None and same_repo and head_ref == manifest.get("head_ref")
    approved, rejected = [], []
    for status, path in rows:
        reason = None
        if applies and status == "A":
            if path in manifest["added_files"]:
                reason = manifest["added_files"][path]
            else:
                for prefix, why in manifest["added_file_patterns"].items():
                    rest = path[len(prefix):]
                    if path.startswith(prefix) and "/" not in rest and SLUG_JSON.match(rest):
                        reason = why
        elif applies and status == "M" and path in manifest["modified_additive_only"]:
            if removed_lines(path) == 0:
                reason = manifest["modified_additive_only"][path]
        elif applies and status == "M" and path in manifest.get("modified_exact", {}):
            entry = manifest["modified_exact"][path]
            if file_sha256(path) == entry["sha256"]:
                reason = entry["reason"]
        (approved if reason else rejected).append((status, path, reason))
    return approved, rejected


def main(argv):
    base, head_ref, same_repo, paths = argv[0], argv[1], argv[2] == "true", argv[4:]
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else None
    rows = changes(base, paths)
    approved, rejected = evaluate(rows, manifest, head_ref, same_repo, lambda p: deletions(base, p))
    scope = "release manifest applies" if manifest and same_repo and head_ref == manifest.get("head_ref") else "strict (no exception)"
    print(f"Protected-path guard: {len(rows)} changed protected file(s); {scope}")
    groups = {}
    for status, path, reason in approved:
        groups.setdefault((status, reason), []).append(path)
    for (status, reason), files in sorted(groups.items()):
        print(f"  approved {status} x{len(files)}: {reason} (e.g. {files[0]})")
    for status, path, _ in rejected:
        print(f"  REJECTED {status} {path}")
    return 1 if rejected else 0


if __name__ == "__main__":
    if len(sys.argv) < 5 or sys.argv[4] != "--":
        sys.exit("usage: verify_protected_changes.py BASE HEAD_REF SAME_REPO(true|false) -- PATH...")
    sys.exit(main(sys.argv[1:]))
