# How It Was Built — Technical Internals

> This document covers the design decisions, architecture, and internals
> of the revision system. For usage, see [README.md](README.md).

---

## Problem Statement

Standard self-study problem:

- Write code → commit → move on → forget in 3 days
- No mechanism forces re-encountering the material
- Anki requires manual card creation — friction means you stop
- Calendar reminders say "revise" but don't show what or why

**Goal:** Zero extra workflow. Hook into what the engineer already does — git commits.

---

## Architecture Overview

```
git commit
    │
    └── .git/hooks/post-commit (bash script)
            │
            ├── python3 auto_add.py
            │       │
            │       ├── reads commit message → extract topic + insight
            │       ├── reads changed files  → detect category
            │       └── writes to revision_db.json (D+1, D+3, D+7)
            │
            └── first commit of day?
                    │
                    yes → python3 revise.py
                              │
                              └── show items due today from revision_db.json
```

---

## Design Decisions

### 1. Git hook as trigger point

`post-commit` fires automatically after every successful commit.
No separate command. No reminder app. No cron job.

It's the exact moment you finish learning something — natural fit.

Hook is installed at `.git/hooks/post-commit` in each repo.
Not committed to the repo itself (`.git/` is never tracked) — installed locally via script.

### 2. First-commit-of-day detection

Showing revision on every commit = noisy, ignored quickly.
Solution: a single date file `.last_shown` tracks when revision was last shown.

```bash
TODAY=$(date +%Y-%m-%d)
TRIGGER_FILE="$REVISION_DIR/.last_shown"

if [ ! -f "$TRIGGER_FILE" ] || [ "$(cat "$TRIGGER_FILE")" != "$TODAY" ]; then
    python3 revise.py          # show today's list
    echo "$TODAY" > "$TRIGGER_FILE"   # mark as shown
fi
```

First commit of the day → file missing or has yesterday's date → show revision.
Subsequent commits → file has today's date → skip silently.

### 3. Commit message parsing

Commit messages already have structure — reuse them instead of a separate form.

```
Add BFS level order — snapshot queue.size() before for loop
 ↑ verb (stripped)     ↑ topic            ↑ key insight (after —)
```

Parsing logic:

```python
for prefix in ["Add ", "Update ", "Create ", "Implement ", "Refactor "]:
    if msg.startswith(prefix):
        msg = msg[len(prefix):]   # strip verb

if " — " in msg:
    topic, note = msg.split(" — ", 1)   # split on em dash
else:
    topic = note = msg   # use full message for both
```

The `—` separator is the standard writing style for good commit messages
("what — why/how") — so adopting it costs nothing extra.

### 4. Category auto-detection

Changed files are read from git:

```python
changed = subprocess.check_output(
    ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"]
).decode().strip().splitlines()
```

Repo root is also read:

```python
repo_root = subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"]
).decode().strip()
```

File path = `repo_name/subfolder/file` — matched against `CATEGORY_MAP` in order.
More specific patterns listed first (e.g. `algorithms/queue` before `algorithms/`).

No config file per repo. Add a new repo under `/Code` → re-run `install_hooks.sh` → done.

### 5. JSON flat file as database

`revision_db.json` — a single JSON file. No SQLite, no Postgres, no setup.

```json
{
  "items": [
    {
      "id": 14,
      "topic": "BFS level order",
      "category": "DSA-Queue",
      "note": "snapshot queue.size() before for loop",
      "file": "algorithms/queue/01_QueueBasics.java",
      "learned": "2026-04-12",
      "revisions": [
        {"due": "2026-04-13", "done": false, "result": null},
        {"due": "2026-04-15", "done": false, "result": null},
        {"due": "2026-04-19", "done": false, "result": null}
      ],
      "buried": false
    }
  ],
  "next_id": 29
}
```

Trade-offs vs SQLite:

| | JSON file | SQLite |
|---|---|---|
| Setup | None | None |
| Queries | Python list filter | SQL |
| Concurrent writes | Not safe | Safe |
| Readable | Yes | No (binary) |
| Size at 1000 items | ~200KB | ~100KB |

At this scale (hundreds of items, single user) JSON is simpler and sufficient.

### 6. Spaced repetition schedule — D+1, D+3, D+7

Based on the Ebbinghaus forgetting curve (1885):

```
Memory retention after learning:
  After 1 day  → ~58% retained
  After 3 days → ~40% retained
  After 7 days → ~25% retained

Each successful recall resets the curve — memory decays slower next time.
```

D+1 / D+3 / D+7 is the minimal effective schedule that catches memory
before it decays past the point of easy retrieval — without being excessive.

### 7. Weak reschedules by appending

When `weak` is called:

- Current pending revision is marked `done: true, result: "❌"`
- Three new revision objects are **appended** to the same item

```python
# Mark current as failed
for rev in item["revisions"]:
    if not rev["done"] and rev["due"] <= str(today):
        rev["done"] = True
        rev["result"] = "❌"
        break

# Append fresh cycle from today
new_revisions = [
    {"due": str(today + timedelta(days=d)), "done": False, "result": None}
    for d in [1, 3, 7]
]
item["revisions"].extend(new_revisions)
```

History is preserved — you can see how many times you struggled with each item.
No data is deleted. `revise.py all` shows the full revision trail.

### 8. Auto-discovery of repos

`install_hooks.sh` scans `$CODE_ROOT/*/.git` — finds every git repo one level deep.

```bash
for GIT_DIR in "$CODE_ROOT"/*/.git; do
    REPO=$(dirname "$GIT_DIR")
    HOOK_FILE="$REPO/.git/hooks/post-commit"
    printf '%s' "$HOOK_SCRIPT" > "$HOOK_FILE"
    chmod +x "$HOOK_FILE"
done
```

No hardcoded repo list. Clone a new repo → re-run the script → it's included.

### 9. DB is gitignored, scripts are committed

```
revision_db.json   → gitignored (personal state, machine-specific)
revise.py          → committed (portable across machines)
auto_add.py        → committed
install_hooks.sh   → committed
seed.py            → committed
```

On a new machine: `git pull` → `bash install_hooks.sh` → `python3 seed.py` → done.
`seed.py` contains the initial dataset — acts as a one-time migration.

---

## File responsibilities

### `auto_add.py`

Called by every post-commit hook. Runs in the context of the repo that was committed.

Responsibilities:
- Read commit message from `git log -1`
- Read changed files from `git diff-tree`
- Read repo root from `git rev-parse --show-toplevel`
- Parse topic + note from commit message
- Detect category from file paths
- Append new item to `revision_db.json` with D+1/D+3/D+7 dates

### `revise.py`

The user-facing CLI. Reads `revision_db.json` and presents/updates items.

Commands:
- `(no args)` — filter items where any revision `due <= today AND done=false`
- `add` — interactive prompt, writes new item
- `done <id>` — find first pending revision due today, set `done=true, result=✅`
- `weak <id>` — mark current as ❌, append new D+1/D+3/D+7 cycle
- `all` — print every item with its revision trail

### `install_hooks.sh`

One-time setup. Writes the hook script to `.git/hooks/post-commit` in each repo.
The hook script itself is a short bash script — calls `auto_add.py` and conditionally `revise.py`.

### `seed.py`

One-time data migration. Contains all topics learned before the system existed.
Each item has `learned_days_ago` — used to back-calculate which revisions are already done.

---

## Adding features

### Add a new skip prefix

In `auto_add.py`:

```python
SKIP_PREFIXES = [
    "fix:", "chore:", ...,
    "docs:"   # ← add here
]
```

### Add a new category

In `auto_add.py`, prepend to `CATEGORY_MAP` (specific patterns first):

```python
CATEGORY_MAP = [
    ("your-new-folder", "YourCategory"),   # ← add at top
    ("queue",           "DSA-Queue"),
    ...
]
```

### Change the revision schedule

In both `auto_add.py` and `seed.py`:

```python
SCHEDULE = [1, 3, 7]   # ← change to e.g. [1, 4, 10, 30] for longer retention
```

### Support nested repos (depth > 1)

Change the glob in `install_hooks.sh` from `/*/.git` to `/**/.git`:

```bash
for GIT_DIR in $(find "$CODE_ROOT" -name ".git" -type d -maxdepth 3); do
```
