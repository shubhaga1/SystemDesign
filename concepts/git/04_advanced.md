# Git — Advanced

Rebase, history rewriting, submodules, backdating commits.

---

## git rebase — linear history

```bash
# Rebase your feature branch on top of latest main
git checkout feature/add-heap
git rebase main
# Takes your commits, replays them on top of latest main
# Result: clean linear history (no merge commit)

# Interactive rebase — edit, squash, reorder last N commits
git rebase -i HEAD~3

# In the editor:
# pick abc1234 Add MaxHeap insert
# squash def5678 Fix typo          ← combine with above
# pick ghi9012 Add extractMax

git rebase --abort     # cancel rebase in progress
git rebase --continue  # continue after resolving conflict
```

```
Merge:   keeps full history, shows branch + merge commit
Rebase:  linear history, all commits appear on one line
Rule:    never rebase shared branches (main) — only your own feature branches
```

---

## Rewriting history — filter-branch

```
git filter-branch = go through EVERY commit, run a command on it, replace it.
Every hash changes → must force push after.
```

### Remove a line from all commit messages

```bash
FILTER_BRANCH_SQUELCH_WARNING=1 \
git filter-branch -f \
  --msg-filter 'grep -v "^Co-Authored-By: Claude"' \
  -- --all

# Word by word:
# FILTER_BRANCH_SQUELCH_WARNING=1  → squelch = silence deprecation warning
# -f                               → force overwrite previous backup refs
# --msg-filter 'cmd'               → pipe each commit message through cmd
# grep -v "^Co-Authored-By: Claude"→ -v = print lines NOT matching
#                                    ^ = line starts with
# -- --all                         → apply to ALL branches

git push --force   # hashes changed — must force push
```

### Change email across all commits

```bash
git filter-branch --env-filter '
    export GIT_AUTHOR_EMAIL="schmuck21@gmail.com"
    export GIT_COMMITTER_EMAIL="schmuck21@gmail.com"
' -- --all

# --env-filter → run shell code for each commit
# export sets env vars Git reads when writing the new commit
git push --force
```

---

## Author date vs Committer date

```
Every commit has TWO dates:

GIT_AUTHOR_DATE    = when you WROTE the code
GIT_COMMITTER_DATE = when the commit was RECORDED

Normally identical. Differ when:
  cherry-pick   → author = original, committer = now
  rebase        → author preserved, committer = rebase time
  filter-branch → committer changes unless you set both

GitHub contribution graph uses AUTHOR DATE
→ set BOTH when backdating to show on correct date
```

```bash
# Backdate a commit
GIT_AUTHOR_DATE="2024-03-15T10:00:00" \
GIT_COMMITTER_DATE="2024-03-15T10:00:00" \
git commit -m "Add SelectionSort"

# Verify both dates
git log --format="%h %ai %ci %s" -1
#              author↑  committer↑
```

---

## Submodules — repo inside a repo

```
submodule = a Git repo nested inside another Git repo
Git tracks it as a REFERENCE (commit hash), not actual files

Symptom of accidental submodule:
  git status shows: modified: security-poc (new commits)
  But files inside are NOT tracked properly
```

### Fix accidental submodule

```bash
# 1. Remove from index (not disk)
git rm --cached security-poc
# --cached = only removes from staging area, files stay on disk

# 2. Delete nested .git
rm -rf security-poc/.git

# 3. Re-add as normal files
git add security-poc/
git commit -m "Fix: convert submodule to regular folder"
git push
```

### Intentional submodules

```bash
git submodule add https://github.com/someone/lib.git libs/lib
git clone --recurse-submodules <url>
git submodule update --init --recursive
```

---

## Real commands used in this project

```bash
# Remove Co-Authored-By from 146 commits in algorithms repo
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch -f \
  --msg-filter 'grep -v "^Co-Authored-By: Claude"' -- --all
git push --force

# Change email across all commits
git filter-branch --env-filter '
    export GIT_AUTHOR_EMAIL="schmuck21@gmail.com"
    export GIT_COMMITTER_EMAIL="schmuck21@gmail.com"
' -- --all
git push --force

# Push rejected after history rewrite
git stash && git push --force && git stash pop

# Delete GitHub repos via CLI
gh repo delete shubhaga1/security-poc --yes
gh repo list shubhaga1
```

---

## Quick reference — all commands

| Command | What it does |
|---|---|
| `git branch -a` | All branches local + remote |
| `git checkout -b <name>` | Create + switch branch |
| `git cherry-pick <hash>` | Apply one commit from another branch |
| `git stash` | Save WIP without committing |
| `git stash pop` | Restore stashed changes |
| `git rebase main` | Replay commits on top of main |
| `git rebase -i HEAD~3` | Interactively edit last 3 commits |
| `git push --force` | Overwrite remote history |
| `git branch -d <name>` | Delete local branch |
| `git push origin --delete <name>` | Delete remote branch |
| `git remote -v` | See remote URL |
| `git branch -vv` | See upstream for each branch |
| `git rev-list --count HEAD` | Total commit count |
| `git shortlog -sn` | Commits per author |
