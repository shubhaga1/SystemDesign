#!/bin/bash
# ============================================================
# Install git post-commit hook in ALL repos under /Code.
# Auto-discovers every git repo — no hardcoded list needed.
# Run once: bash install_hooks.sh
# Re-run anytime you clone a new repo.
# ============================================================

CODE_ROOT="/Users/shubhamgarg/Downloads/Code"
REVISION_DIR="$CODE_ROOT/SystemDesign/revision"

HOOK_SCRIPT='#!/bin/bash
REVISION_DIR="/Users/shubhamgarg/Downloads/Code/SystemDesign/revision"
TODAY=$(date +%Y-%m-%d)
TRIGGER_FILE="$REVISION_DIR/.last_shown"

# Step 1: Auto-add this commit to the revision DB
python3 "$REVISION_DIR/auto_add.py"

# Step 2: First commit of the day → show today'"'"'s revision list
if [ ! -f "$TRIGGER_FILE" ] || [ "$(cat "$TRIGGER_FILE")" != "$TODAY" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  FIRST COMMIT OF THE DAY — Here is what to revise today:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 "$REVISION_DIR/revise.py"
    echo "$TODAY" > "$TRIGGER_FILE"
fi
'

echo "Scanning $CODE_ROOT for git repos..."
echo ""

COUNT=0

# Find every .git folder directly under CODE_ROOT (depth 2 = repo/.git)
for GIT_DIR in "$CODE_ROOT"/*/.git; do
    REPO=$(dirname "$GIT_DIR")
    HOOK_FILE="$REPO/.git/hooks/post-commit"

    # Skip the revision dir's own repo if it has no separate .git
    printf '%s' "$HOOK_SCRIPT" > "$HOOK_FILE"
    chmod +x "$HOOK_FILE"
    echo "  ✅ $(basename $REPO)"
    COUNT=$((COUNT + 1))
done

echo ""
echo "Installed in $COUNT repos."
echo ""
echo "How it works:"
echo "  Every git commit → auto_add.py runs → adds to revision DB"
echo "  First commit of the day → revise.py runs → shows today's items"
echo ""
echo "Commit message format:"
echo "  Add <Topic> — <Key insight>"
echo "  Example: Add Kth Largest — min heap size k, poll when >k, peek=answer"
