#!/usr/bin/env bash
# scripts/deploy.sh — sync docs/3d-viewer/ to the gh-pages branch and push.
# Local build is the source of truth; this is the "no CI" deploy path.
#
# Run via `make deploy` so the build is fresh.

set -euo pipefail

VIEWER_DIR="docs/3d-viewer"
BRANCH="gh-pages"
TMP="$(mktemp -d -t daisy-deploy.XXXXXXXX)"

cleanup() {
  git worktree remove --force "$TMP" 2>/dev/null || rm -rf "$TMP"
}
trap cleanup EXIT

echo "deploying $VIEWER_DIR/ → origin/$BRANCH via worktree $TMP"

# Make sure something to deploy actually exists.
if [ ! -f "$VIEWER_DIR/model.glb" ] || [ ! -f "$VIEWER_DIR/index.html" ]; then
  echo "ERROR: $VIEWER_DIR is missing build outputs. Run \`make build\` first." >&2
  exit 1
fi

# Set up the worktree on the gh-pages branch. `git worktree add --orphan`
# was added in git 2.42; build the empty initial commit via plumbing instead,
# which works on any git.
if ! git ls-remote --exit-code --heads origin "$BRANCH" >/dev/null 2>&1; then
  echo "  bootstrapping empty $BRANCH on origin (first deploy)"
  empty_tree=$(git mktree </dev/null)
  init_commit=$(printf 'init %s\n' "$BRANCH" | git commit-tree "$empty_tree")
  git push origin "$init_commit:refs/heads/$BRANCH"
fi

git fetch --quiet origin "$BRANCH"
git worktree add -B "$BRANCH" "$TMP" "origin/$BRANCH" >/dev/null

# Sync the built site into the worktree (delete anything stale).
rsync -a --delete --exclude=.git "$VIEWER_DIR/" "$TMP/"

cd "$TMP"
git add -A
if git diff --cached --quiet; then
  echo "  no changes vs origin/$BRANCH — nothing to push"
else
  git commit -m "deploy $(date -u +%Y-%m-%dT%H:%MZ)" --quiet
  git push -f origin "$BRANCH"
  echo "  pushed."
fi
