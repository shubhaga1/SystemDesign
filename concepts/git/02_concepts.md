# Git — Core Concepts

---

## What is Git?

Git tracks changes to files over time — a save history you can go back to.

```
Your files  →  Staging area  →  Local repo  →  Remote repo (GitHub)
(working)       (git add)        (git commit)    (git push)
```

---

## What is a commit?

A commit = a snapshot of your entire project at a point in time.

```
Each commit has:
  hash     → unique ID: abc1234 (SHA-1 of content)
  message  → what you wrote
  author   → who made it
  date     → when (two dates — see advanced guide)
  parent   → previous commit hash (linked list of snapshots)

abc1234 → def5678 → ghi9012 → HEAD
(oldest)                      (latest)
```

---

## What is HEAD?

```
HEAD = pointer to the commit you're currently on
       (usually = tip of your current branch)

Normal:    HEAD → main → latest commit
Detached:  HEAD → specific commit (not on any branch)
           → happens when you git checkout abc1234
           → commits made here are lost unless you create a branch
```

---

## Branches

```
Branch = a pointer to a commit. Moving it forward = making commits.

main  ──────────────────────────── (stable, production)
         \
          feature/add-heap ──────  (your work in progress)
```

```bash
git branch                  # see local branches (* = current)
git branch -a               # see ALL branches (local + remote)
git branch -r               # remote branches only
git checkout -b feature/xyz # create + switch to new branch
git checkout main           # switch back
git merge feature/xyz       # merge into current branch
git branch -d feature/xyz   # delete after merging
```

---

## Remote, Origin, Upstream

```
remote    = a nickname for a GitHub URL
origin    = default nickname (what you cloned from)
upstream  = which remote branch your local branch tracks
            (where git push/pull go by default)
```

```bash
git remote -v               # see remote URL
git remote add origin <url> # add remote (after git init)
git push -u origin main     # push + set upstream in one step
                            # after this: git push works alone
git branch -vv              # see upstream for each branch
```

---

## .gitignore — files to never track

```bash
# .gitignore in project root
target/          # compiled .class files
*.class          # Java bytecode
.DS_Store        # macOS junk
.idea/           # IntelliJ project folder
*.env            # secrets — NEVER commit
```

Files listed here are invisible to git status.

---

## What .git folder contains

```
.git/
  HEAD          → current branch pointer
  config        → repo config (remote URL, branch tracking)
  objects/      → all file content stored by hash
  refs/heads/   → local branches
  refs/remotes/ → remote branches
  index         → staging area (what's git add-ed)
  ORIG_HEAD     → backup before dangerous operations
```

```bash
cat .git/HEAD
# ref: refs/heads/main

cat .git/refs/heads/main
# abc1234...  (the commit hash main points to)
```

Git stores everything by content hash — same content = same hash. This is why git is fast and efficient.

---

## Double dash vs single dash

```
--word   = long option  (readable, use in scripts)
-letter  = short option (fast to type)

git log --oneline    same as   git log (but condensed)
git log -5           same as   git log --max-count=5
git push --force     same as   git push -f
git commit --message same as   git commit -m
git branch --all     same as   git branch -a
```

No technical difference — purely style.
