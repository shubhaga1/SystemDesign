# Git — Daily Usage

The commands you use every single day.

---

## The 5-step workflow

```
1. Write/edit code
2. git status       → see what changed
3. git add          → stage the changes
4. git commit       → save a snapshot
5. git push         → upload to GitHub
```

```bash
# Check what changed
git status

# Stage files
git add tree/BST.java       # one file
git add tree/               # whole folder
git add .                   # everything

# Commit
git commit -m "Add Trie insert and search"
git commit -am "Fix off-by-one in BubbleSort"
# -am = stage all MODIFIED files + commit in one step
# ⚠️  -a does NOT stage new untracked files — use git add for those

# Push to GitHub
git push

# Download latest from GitHub
git pull
```

---

## git status — understand the output

```bash
git status

# On branch main                        ← which branch you're on
#
# Changes to be committed:              ← staged (will go in next commit)
#     modified:   tree/BST.java
#
# Changes not staged for commit:        ← changed but NOT staged yet
#     modified:   recursion/Factorial.java
#
# Untracked files:                      ← new files Git doesn't know about
#     array/LinearSearch.java
```

---

## git diff vs git status

```
git status    → WHAT files changed (names only)
git diff      → WHAT changed inside those files (actual lines)

git diff              → unstaged changes (before git add)
git diff --staged     → staged changes (after git add, before commit)
git diff HEAD         → all changes staged + unstaged combined
git diff abc123 def456→ difference between two commits
```

---

## git log — see history

```bash
git log --oneline           # compact, one line per commit
git log --oneline -5        # last 5 commits only
git log --oneline tree/BST.java  # commits that touched this file
git show abc1234            # full diff of a specific commit
```

---

## Commit message rules

```
✅ "Add BFS shortest path with parent tracking"
✅ "Fix null pointer in MaxHeap when tree is empty"
❌ "updated BST.java"
❌ "changes"
❌ "fix"
```

| Type | When |
| --- | --- |
| `Add` | New file or feature |
| `Fix` | Bug fix |
| `Update` | Change to existing feature |
| `Remove` | Delete code or files |
| `Move` | Move files between folders |

Rules:
- Present tense, imperative: "Add" not "Added"
- Max 72 characters
- One commit = one logical change
- Answer what + why, not how

---

## Undoing mistakes

```bash
# Unstage a file (before commit)
git restore --staged tree/BST.java

# Discard edits in a file (CANNOT undo — dangerous)
git restore tree/BST.java

# Undo last commit, keep the changes
git reset HEAD~1

# Undo last 2 commits
git reset HEAD~2
```

---

## Quick reference

| Command | What it does |
|---|---|
| `git status` | See what changed |
| `git add <file>` | Stage a file |
| `git add .` | Stage everything |
| `git commit -m "msg"` | Save snapshot |
| `git commit -am "msg"` | Stage modified + commit |
| `git push` | Upload to GitHub |
| `git pull` | Download from GitHub |
| `git log --oneline` | See history |
| `git diff` | See unstaged changes |
| `git diff --staged` | See staged changes |
| `git restore <file>` | Discard file changes |
| `git restore --staged <file>` | Unstage a file |
| `git reset HEAD~1` | Undo last commit |
| `git show <hash>` | See a commit's changes |
