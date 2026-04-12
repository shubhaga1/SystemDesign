# Revision System — Spaced Repetition for Engineers

An automated spaced repetition system that hooks into your git workflow.
No apps, no Anki cards, no manual tracking — just commit your code and it runs.

---

## How it works (user view)

### Normal day

```
You write code → git commit → hook fires automatically
  ↓
On your FIRST commit of the day:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    FIRST COMMIT OF THE DAY — Here is what to revise today:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [DSA-Queue]
    ID=14  D+1   BFS level order — snapshot queue.size()
    ID=19  D+3   Sliding Window Maximum — monotonic Deque

  [SystemDesign]
    ID=7   D+7   Web Crawler capacity — 100TB not 10PB
  ↓
After reviewing each item → mark done or weak:
  python3 revise.py done 14   → ✅ remembered → next date auto-scheduled
  python3 revise.py weak 19   → ❌ forgot → full D+1/D+3/D+7 from today
```

### Your daily routine (2 min total)

```
1. Make your first git commit (any repo)
   → revision list appears automatically in the terminal

2. Spend 30 sec per item:
   - Close your notes
   - Try to explain the concept aloud / write the key line from memory
   - Open the file to verify

3. Mark each item:
   python3 revise.py done <id>   → got it
   python3 revise.py weak <id>   → forgot

That's it. Zero extra workflow.
```

---

## Commands

```bash
# Run from anywhere — full path or cd first
cd /Users/shubhamgarg/Downloads/Code/SystemDesign/revision

python3 revise.py              # show today's items (also auto-shown on first commit)
python3 revise.py add          # manually add something (interactive prompts)
python3 revise.py done <id>    # mark item as remembered ✅
python3 revise.py weak <id>    # mark as forgotten ❌ → reschedules D+1/D+3/D+7 from today
python3 revise.py all          # show full log with all items and statuses
```

---

## Commit message format

The hook reads your commit message to extract topic and insight automatically.

```
Add <Topic> — <Key insight one line>
     ↑           ↑
     topic       used as the revision reminder note

Examples:
  Add BFS level order — snapshot queue.size() before for loop
  Add Kth Largest — min heap size k, poll when size>k, peek=kth
  Add Cassandra vs MySQL — distributed writes, no master, partition key=domain
  Add DEK/KEK pattern — DEK=AES per record, KEK=RSA wraps DEK, rotate=re-wrap DEKs only
```

**The `—` separator is important** — everything after it becomes your recall hint.

Commits that are skipped (not added to revision):
```
fix: ...        chore: ...      merge ...
Merge ...       wip ...         WIP ...
Add revision    Update revision
```

---

## Spaced repetition schedule

```
You learn something → it gets scheduled 3 times:
  Day +1  → recall after 1 day  (short-term consolidation)
  Day +3  → recall after 3 days (medium-term)
  Day +7  → recall after 7 days (long-term)

If you mark ❌ (forgot) → full cycle restarts from today:
  Today → D+1, D+3, D+7 again

If you mark ✅ (remembered) all 3 → topic is mastered.

Why these intervals?
  Based on Ebbinghaus forgetting curve.
  Memory decays exponentially. Each successful recall extends retention.
  D+1/D+3/D+7 is the minimal effective schedule proven by research.
```

---

## File structure

```
revision/
  revise.py          ← main CLI (show today, add, done, weak, all)
  auto_add.py        ← called by git hook on every commit
  install_hooks.sh   ← run once to set up hooks in all repos
  seed.py            ← one-time script to load past learnings into DB
  revision_db.json   ← your personal DB (gitignored, stays local)
  .gitignore         ← excludes revision_db.json from commits
  README.md          ← this file
```

---

## How it was built (developer view)

### Problem it solves

Standard problem with self-study:
- You write code → commit → move on → forget in 3 days
- No mechanism forces you to re-encounter the material
- Anki requires manual card creation (friction = you stop doing it)
- Calendar reminders don't show content — just "revise something"

### Design decisions

**1. Git hook as the trigger point**
Git `post-commit` hook runs automatically after every commit — zero extra effort.
It's the natural moment when you've just finished learning something.
Hook location: `.git/hooks/post-commit` in each repo.

**2. First-commit-of-day detection**
Problem: showing revision on every commit would be noisy.
Solution: write today's date to `.last_shown` file after first trigger.
Check: `if file doesn't exist OR file content != today → show revision`.

```bash
TODAY=$(date +%Y-%m-%d)
TRIGGER_FILE="$REVISION_DIR/.last_shown"

if [ ! -f "$TRIGGER_FILE" ] || [ "$(cat $TRIGGER_FILE)" != "$TODAY" ]; then
    python3 revise.py
    echo "$TODAY" > "$TRIGGER_FILE"
fi
```

**3. Commit message parsing**
Topic and insight extracted from commit message automatically.
No separate form to fill. The format `Add X — Y` is already a good commit message style.

```python
# "Add BFS level order — snapshot queue.size() before for loop"
if " — " in msg:
    topic = msg.split(" — ")[0]   # "Add BFS level order"
    note  = msg.split(" — ")[1]   # "snapshot queue.size() before for loop"
```

Common prefixes (Add, Update, Create) are stripped from topic.

**4. Category auto-detection from file paths**
Changed files are read from `git diff-tree --name-only HEAD`.
File path is pattern-matched against a priority list.

```python
CATEGORY_MAP = [
    ("algorithms/queue",  "DSA-Queue"),
    ("algorithms/tree",   "DSA-Tree"),
    ("encryption/",       "Encryption"),
    ("kafka",             "Kafka"),
    ...
]
```

**5. JSON flat file as DB**
`revision_db.json` — simple JSON array. No database setup needed.
Each item stores: id, topic, category, note, file, learned date, revisions array.
Each revision: `{due, done, result}`.

```json
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
```

**6. `weak` reschedules by appending — not replacing**
When you mark weak, the existing failed revision is marked done (result=❌),
then 3 new revision objects are appended to the same item's revisions array.
History is preserved. You can see how many times you struggled.

**7. gitignore for DB, not scripts**
`revision_db.json` is gitignored — it's personal state, machine-specific.
Scripts are committed — pull them on any machine, run `seed.py` once.

---

## Setup from scratch (on a new machine)

```bash
# 1. Clone SystemDesign repo (scripts live here)
git clone https://github.com/shubhaga1/SystemDesign.git
cd SystemDesign/revision

# 2. Install hooks in all repos
bash install_hooks.sh

# 3. Seed past learnings (one-time)
python3 seed.py

# 4. Verify
python3 revise.py all
```

---

## Adding a new repo to the system

Edit `install_hooks.sh` — add the repo path to the REPOS array:

```bash
REPOS=(
    "/Users/shubhamgarg/Downloads/Code/SystemDesign"
    "/Users/shubhamgarg/Downloads/Code/algorithms"
    "/Users/shubhamgarg/Downloads/Code/learning-journal"
    "/Users/shubhamgarg/Downloads/Code/your-new-repo"    # ← add here
)
```

Then run `bash install_hooks.sh` again.

---

## Adding a new category

Edit `auto_add.py` — add a pattern to `CATEGORY_MAP`:

```python
CATEGORY_MAP = [
    ("algorithms/queue",  "DSA-Queue"),
    ("your-new-folder",   "YourCategory"),   # ← add here
    ...
]
```

Categories are matched in order — put more specific patterns first.
