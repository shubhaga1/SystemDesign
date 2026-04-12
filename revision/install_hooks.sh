#!/bin/bash
# ============================================================
# Install git post-commit hook in ALL learning repos.
# Run once: bash install_hooks.sh
# After this, every `git commit` auto-adds to revision DB.
# ============================================================

REPOS=(
    "/Users/shubhamgarg/Downloads/Code/SystemDesign"
    "/Users/shubhamgarg/Downloads/Code/algorithms"
    "/Users/shubhamgarg/Downloads/Code/learning-journal"
)

HOOK_CONTENT='#!/bin/bash
# Auto-add to revision DB on every commit
python3 /Users/shubhamgarg/Downloads/Code/SystemDesign/revision/auto_add.py
'

for REPO in "${REPOS[@]}"; do
    HOOK_FILE="$REPO/.git/hooks/post-commit"

    if [ ! -d "$REPO/.git" ]; then
        echo "⚠️  Skipping $REPO — not a git repo"
        continue
    fi

    echo "$HOOK_CONTENT" > "$HOOK_FILE"
    chmod +x "$HOOK_FILE"
    echo "✅ Hook installed: $REPO"
done

echo ""
echo "Done! Every git commit now auto-adds to:"
echo "  /Users/shubhamgarg/Downloads/Code/SystemDesign/revision/revision_db.json"
echo ""
echo "Commit message format for best results:"
echo "  Add <Topic> — <Key insight one line>"
echo "  Example: Add BFS level order — snapshot queue.size() before for loop"
