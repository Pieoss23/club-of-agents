#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:?role required}"
TASK_ID="${2:?task id required}"
SLUG="${3:?short slug required}"

BRANCH="agent/${ROLE}/${TASK_ID}-${SLUG}"
WORKTREE="../project-${ROLE}-${TASK_ID}"

git fetch origin
git worktree add "$WORKTREE" -b "$BRANCH" origin/main

echo "Created:"
echo "  branch:   $BRANCH"
echo "  worktree: $WORKTREE"
