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

### Two starting scenarios

**Scenario A — cloned from GitHub (most common):**
```bash
git clone https://github.com/shubhaga1/algorithms.git
# origin is set AUTOMATICALLY — git remembers where you cloned from
git remote -v   # already shows origin URL
git push        # works immediately, no setup needed
```

**Scenario B — started locally with git init:**
```bash
mkdir algorithms && cd algorithms
git init        # local repo created, NO remote yet
git add .
git commit -m "first commit"

git push        # ❌ ERROR: no remote configured — git doesn't know where to push
```

You must connect it to GitHub yourself. **3 ways to do this:**

```bash
# Way 1 — manual: create repo on GitHub first, then link
git remote add origin https://github.com/shubhaga1/algorithms.git
git push -u origin main

# Way 2 — GitHub CLI: creates GitHub repo AND links in one command
gh repo create algorithms --public --source . --remote origin --push
# --source .     = use current folder
# --remote origin= name it "origin"
# --push         = push immediately

# Way 3 — GitHub CLI: create repo only, push separately
gh repo create algorithms --public
git remote add origin https://github.com/shubhaga1/algorithms.git
git push -u origin main
```

```bash
# Other remote commands
git remote -v                    # see current remote URL
git remote set-url origin <url>  # change remote URL
git remote remove origin         # remove remote (local repo stays)
git branch -vv                   # see upstream for each branch
```

**In this project:** algorithms repo was started with `git init` locally,
so we used `gh repo create` (Way 2) to create and link in one step.

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

## fetch vs pull vs push

```
fetch  = download changes from remote, but do NOT apply to your branch
         → updates origin/main pointer, your local main is untouched
         → safe — never changes your working files

pull   = fetch + merge in one step
         → downloads AND applies changes to your current branch
         → git pull = git fetch + git merge origin/main

push   = upload your local commits to remote
         → opposite of pull
```

```bash
git fetch                  # download, don't apply
git fetch origin           # same, explicit remote name

git log origin/main        # see what was fetched (remote state)
git diff main origin/main  # compare your branch vs fetched remote

git pull                   # fetch + merge (most common)
git pull --rebase          # fetch + rebase (cleaner history)

git push                   # upload your commits
git push -u origin main    # push + set upstream
git push --force           # overwrite remote (after history rewrite)
```

**When to use fetch vs pull:**
```
fetch:  you want to see what changed on remote before merging
        safe to run anytime, won't break anything

pull:   you're ready to bring in remote changes now
        risky if you have local uncommitted changes — stash first

push:   you finished work and want it on GitHub
```

```
Timeline:

Your machine:   A → B → C (main)
GitHub:         A → B → D (someone else pushed D)

git fetch:      downloads D, updates origin/main → D
                your main still at C, nothing changed in your files

git pull:       downloads D + merges → your main becomes A→B→C+D merge
                or with --rebase: A→B→D→C (your C on top)

git push:       would FAIL (not fast-forward)
                must pull/rebase first, then push
```

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
