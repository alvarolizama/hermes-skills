#!/bin/bash
# Sync pocketbrain runtime → repo
# Uso: ./sync_repo.sh

RUNTIME=~/.hermes/skills/productivity/pocketbrain
REPO=~/Workspace/repos/skills/hermes-skills/pocketbrain

echo "=== Syncing pocketbrain runtime → repo ==="

# SKILL.md
cp "$RUNTIME/SKILL.md" "$REPO/SKILL.md"
echo "✓ SKILL.md"

# References
for f in "$RUNTIME/references/"*.md; do
    cp "$f" "$REPO/references/"
done
echo "✓ references/"

# Scripts (only .py and .sh)
for f in "$RUNTIME/scripts/"*.py "$RUNTIME/scripts/"*.sh; do
    cp "$f" "$REPO/scripts/"
done
echo "✓ scripts/"

# JS/CSS/HTML assets
for f in "$RUNTIME/scripts/"*.js "$RUNTIME/scripts/"*.css "$RUNTIME/scripts/"*.html; do
    cp "$f" "$REPO/scripts/"
done
echo "✓ web assets"

cd "$REPO/.." || exit 1
echo ""
echo "=== git diff --stat ==="
git diff --stat pocketbrain/
echo ""
echo "Listo. Revisa el diff y commit:"
echo "  cd ~/Workspace/repos/skills/hermes-skills && git add pocketbrain/ && git commit -m '...' && git push"
