#!/usr/bin/env bash
# Publish only the validated, staged snapshot. Never overwrite concurrent production changes.
set -euo pipefail
if git diff --cached --quiet; then
  exit 0
fi
base=$(git rev-parse HEAD)
mapfile -d '' staged_paths < <(git diff --cached --name-only -z)
git commit -m "Refresh CFBD season snapshot"
git fetch origin main
# Never combine independently generated data bundles, even when Git could merge their text.
# A fresh current-main run must re-derive and re-validate the whole bundle instead.
if [ -n "$(git diff --name-only "$base" origin/main -- "${staged_paths[@]}")" ]; then
  echo 'Refresh overlaps newer production data; no push performed. Run a fresh current-main refresh.' >&2
  exit 1
fi
if ! git rebase origin/main; then
  # Leave readable, validated JSON for the always-running keeper/monitor step.
  # Recovery is a fresh current-main workflow run, not conflict resolution by overwriting data.
  git rebase --abort
  echo 'Refresh conflicts with newer production data; no push performed. Run a fresh current-main refresh.' >&2
  exit 1
fi
git push origin HEAD:main
