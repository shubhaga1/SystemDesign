# Revision System — Spaced Repetition for Engineers

An automated spaced repetition system built into your git workflow.
No apps. No Anki cards. No manual tracking. Just commit code and it runs.

---

## What it does

Every time you `git commit` in any learning repo:
- Automatically adds the topic to your revision schedule (D+1, D+3, D+7)
- On your **first commit of the day** → shows exactly what to revise today

---

## Files

| File | Purpose |
|------|---------|
| `revise.py` | Main CLI — show today, add, done, weak, all |
| `auto_add.py` | Called by git hook on every commit |
| `install_hooks.sh` | Run once — installs hooks in all repos under `/Code` |
| `seed.py` | One-time — loads past learnings into DB |
| `revision_db.json` | Your personal DB (gitignored, stays local) |
| `README.md` | User guide (this file) |
| `HOW_IT_WAS_BUILT.md` | Technical deep dive — design decisions and internals |

---

## Setup (first time)

```bash
cd /Users/shubhamgarg/Downloads/Code/SystemDesign/revision

# 1. Install hooks in all repos under /Code (auto-discovers all)
bash install_hooks.sh

# 2. Load past learnings into DB (one-time)
python3 seed.py

# 3. Verify
python3 revise.py all
```

---

## Daily workflow

```
1. Make your first git commit of the day (any repo)

   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
     FIRST COMMIT OF THE DAY — Here is what to revise today:
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   [DSA-Queue]
     ID=14  D+1   BFS level order — snapshot queue.size()
     ID=19  D+3   Sliding Window Maximum — monotonic Deque
   [SystemDesign]
     ID=7   D+7   Web Crawler capacity — 100TB not 10PB

2. For each item (30 sec each):
   - Close your notes
   - Try to recall the key insight from memory
   - Open the file to verify

3. Mark each item:
   python3 revise.py done 14   → ✅ remembered
   python3 revise.py weak 19   → ❌ forgot → reschedules from today
```

---

## Commands

```bash
python3 revise.py              # show today's revision items
python3 revise.py add          # manually add a topic (interactive)
python3 revise.py done <id>    # mark as remembered ✅
python3 revise.py weak <id>    # mark as forgotten ❌ → reschedule D+1/D+3/D+7
python3 revise.py all          # show all items and their status
python3 revise.py review       # ask Claude to audit today's items for clarity
```

### What `review` does

Runs `claude` on today's output and asks it to:

- Flag any key insight that is too vague to recall from
- Suggest a sharper one-liner for weak insights
- Score ease-of-learning 1–5

```bash
python3 revise.py review
# → 🤖 Asking Claude to review your revision output...
# → Claude prints suggestions directly in terminal
```

---

## Commit message format

The hook auto-extracts topic and insight from your commit message.

```
Add <Topic> — <Key insight>

Examples:
  Add BFS level order — snapshot queue.size() before for loop
  Add Kth Largest — min heap size k, poll when >k, peek=answer
  Add DEK/KEK pattern — DEK=AES per record, KEK wraps DEK, rotate=re-wrap DEKs only
```

The `—` separator splits topic from hint. Everything after it is shown during revision.

**Commits that are skipped** (not added to revision):
```
fix:  chore:  merge  Merge  wip  WIP  Add revision  seed
```

---

## Spaced repetition schedule

```
Learn something → scheduled 3 times automatically:
  D+1  → next day           (short-term consolidation)
  D+3  → 3 days later       (medium-term)
  D+7  → 1 week later       (long-term)

Mark ✅ all 3 times → topic mastered
Mark ❌ → full D+1/D+3/D+7 cycle restarted from today
```

Based on the Ebbinghaus forgetting curve — memory decays fast,
each successful recall extends how long it sticks.

---

## New machine setup

```bash
git clone https://github.com/shubhaga1/SystemDesign.git
cd SystemDesign/revision
bash install_hooks.sh    # installs in all repos under /Code
python3 seed.py          # reload past learnings
python3 revise.py        # verify
```

---

## Add a new repo

Just clone it under `/Code` and re-run:
```bash
bash install_hooks.sh    # auto-discovers all repos — no config needed
```

---

## Add a new category

Edit `auto_add.py` — prepend to `CATEGORY_MAP`:
```python
CATEGORY_MAP = [
    ("your-new-folder", "YourCategory"),   # ← add at top (specific first)
    ("queue",           "DSA-Queue"),
    ...
]
```

> For technical internals — how the hook works, DB schema, design decisions:
> see [HOW_IT_WAS_BUILT.md](HOW_IT_WAS_BUILT.md)
