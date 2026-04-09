# Git — Intermediate

Branches, checkout, stash, cherry-pick, merge conflicts.

---

## Branches — full workflow

```bash
# Create + switch
git checkout -b feature/add-heap
git switch -c feature/add-heap     # modern equivalent

# Work, commit as usual
git add heap/MaxHeap.java
git commit -m "Add MaxHeap insert and extractMax"

# Push branch to GitHub
git push -u origin feature/add-heap

# Switch back and merge
git checkout main
git merge feature/add-heap

# Delete after merge
git branch -d feature/add-heap           # local
git push origin --delete feature/add-heap # remote
```

---

## git checkout — navigate your repo

```bash
# Switch branch
git checkout main
git checkout feature/add-heap

# Go to a specific commit (detached HEAD)
git checkout abc1234
# ⚠️  You're not on any branch — commits here will be lost
# Save them: git checkout -b fix/from-old-commit

# Restore one file from a specific commit
git checkout abc1234 -- tree/BST.java

# Restore file to last committed state
git checkout -- tree/BST.java    # same as: git restore tree/BST.java
```

---

## git stash — save work without committing

```bash
# Save current changes (working dir is now clean)
git stash

# See stashed items
git stash list
# stash@{0}: WIP on main: abc1234 Add BST

# Restore
git stash pop        # restore + delete from stash
git stash apply      # restore but keep in stash

# Named stash
git stash push -m "half-done heap"

# Drop without applying
git stash drop stash@{0}
git stash clear      # remove all stashes
```

When to use:
```
You're mid-feature, need to switch branches fast
git pull blocked by local changes
Quick experiment — stash, try, pop back
```

---

## git cherry-pick — grab one commit from another branch

```bash
# Find the commit you want
git log --oneline feature/add-heap
# abc1234 Fix null pointer in MaxHeap insert   ← want this
# def5678 Add MaxHeap (half done)              ← don't want this

# Switch to target branch
git checkout main

# Apply just that commit
git cherry-pick abc1234
# Creates a NEW commit on main with same changes

# Apply without auto-committing (review first)
git cherry-pick --no-commit abc1234

# Range of commits
git cherry-pick abc1234^..def5678
```

When to use:
```
✅ Hotfix on feature branch needs to go to main immediately
✅ Backport fix to older release branch
✅ Accidentally committed on wrong branch
❌ Don't use for whole features — use merge instead
```

---

## Merge conflicts

```bash
git merge feature/add-heap
# CONFLICT (content): Merge conflict in tree/BST.java

# Open the file — Git marks the conflict:
<<<<<<< HEAD
    return null;          ← your version (main)
=======
    return node.left;     ← incoming (feature branch)
>>>>>>> feature/add-heap

# Edit the file to keep what you want, remove the markers
# Then:
git add tree/BST.java
git commit -m "Merge feature/add-heap — keep node.left fix"

# Abort if you want to undo the merge
git merge --abort
```

---

## Common errors and fixes

```bash
# "rejected — non-fast-forward"
# Someone else pushed, your history is behind
git pull --rebase     # put their commits first, yours on top
git push

# "Accidentally committed to wrong branch"
git log --oneline -1          # note the hash: abc1234
git reset HEAD~1              # undo commit, keep changes
git checkout correct-branch
git add .
git commit -m "same message"

# "Untracked files not going away after .gitignore"
git rm -r --cached .          # untrack everything
git add .                     # re-add respecting .gitignore
git commit -m "Fix gitignore"
```

---

## Git metrics

```bash
git rev-list --count HEAD          # total commits
git shortlog -sn                   # commits per author
git log --stat --oneline | head -20 # lines changed per commit
du -sh .git                        # repo size
git log --format="%an <%ae>" | sort -u  # all contributors
```
