#!/bin/bash
# Collect all student submissions from their branches into main.
# Run this at the submission deadline (0:45).
#
# Usage: bash collect.sh

set -e

echo "=== Collecting student submissions ==="
echo ""

# Make sure we're on main and up to date
git checkout main
git pull origin main

# Fetch all remote branches
git fetch --all

echo ""
echo "=== Remote branches found ==="
git branch -r | grep -v HEAD | grep -v main

echo ""
echo "=== Merging student branches ==="

for branch in $(git branch -r | grep -v HEAD | grep -v main | sed 's/origin\///'); do
    echo -n "  Merging $branch... "
    if git merge "origin/$branch" --no-edit -m "Merge $branch" 2>/dev/null; then
        echo "OK"
    else
        echo "CONFLICT — skipping (student can resubmit)"
        git merge --abort 2>/dev/null || true
    fi
done

echo ""
echo "=== Submissions collected ==="
echo ""
echo "Red teams:"
ls submit/red_*/malicious_pr.diff 2>/dev/null || echo "  (none)"
echo ""
echo "Blue teams:"
ls submit/blue_*/agent.py 2>/dev/null || echo "  (none)"
echo ""
echo "Ready to score:"
echo "  python score.py --red submit/red_* --blue submit/blue_*"
