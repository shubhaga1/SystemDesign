#!/usr/bin/env python3
"""
Called by git post-commit hook automatically.
Reads commit message + changed files → adds to revision DB.

Commit message format (two styles):
  Style 1 (with insight after —):
    Add BFS level order — snapshot queue.size() before for loop
    ↑ topic                ↑ key insight (auto-extracted)

  Style 2 (no insight):
    Add Queue basics — FIFO API, BFS level order, shortest path
    ↑ used as both topic and note

Skip revision if commit message starts with:
  fix: / chore: / merge / Merge / wip / WIP / Add revision
"""

import sys
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

# Always write to SystemDesign/revision/revision_db.json
# regardless of which repo the commit was in
REVISION_DIR = Path("/Users/shubhamgarg/Downloads/Code/SystemDesign/revision")
DB_FILE = REVISION_DIR / "revision_db.json"
SCHEDULE = [1, 3, 7]

# Map file path patterns → revision category
CATEGORY_MAP = [
    ("algorithms/queue",        "DSA-Queue"),
    ("algorithms/tree",         "DSA-Tree"),
    ("algorithms/stack",        "DSA-Stack"),
    ("algorithms/array",        "DSA-Array"),
    ("algorithms/sorting",      "DSA-Sorting"),
    ("algorithms/graph",        "DSA-Graph"),
    ("algorithms/recursion",    "DSA-Recursion"),
    ("algorithms/hashmap",      "DSA-HashMap"),
    ("algorithms/slidingWindow","DSA-SlidingWindow"),
    ("algorithms/java8",        "Java"),
    ("algorithms/fundamentals", "Java"),
    ("algorithms/",             "DSA"),
    ("encryption/",             "Encryption"),
    ("sql/",                    "SQL"),
    ("system-design/",          "SystemDesign"),
    ("spark/",                  "SystemDesign"),
    ("kafka",                   "Kafka"),
    ("docker-k8s",              "K8s"),
    ("huggingface",             "ML"),
    ("langchain",               "ML"),
    ("vllm",                    "ML"),
    ("vector-db",               "ML"),
    ("git/",                    "Git"),
    ("python/",                 "Python"),
]

SKIP_PREFIXES = [
    "fix:", "chore:", "merge", "Merge", "wip", "WIP",
    "Add revision", "Update revision", "seed", "Seed"
]


def detect_category(changed_files):
    """Detect revision category from changed file paths."""
    for f in changed_files:
        for pattern, category in CATEGORY_MAP:
            if pattern in f:
                return category
    return "General"


def parse_commit_message(msg):
    """
    Extract topic and note from commit message.
    'Add BFS level order — snapshot queue.size() before for loop'
    → topic: 'BFS level order'
    → note:  'snapshot queue.size() before for loop'
    """
    msg = msg.strip()

    # Remove common prefixes: Add, Update, Fix, etc.
    for prefix in ["Add ", "Update ", "Create ", "Implement ", "Refactor "]:
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
            break

    # Split on em dash or double dash
    if " — " in msg:
        parts = msg.split(" — ", 1)
        topic = parts[0].strip()
        note  = parts[1].strip()
    elif " -- " in msg:
        parts = msg.split(" -- ", 1)
        topic = parts[0].strip()
        note  = parts[1].strip()
    else:
        topic = msg
        note  = msg   # use full message as note if no separator

    # Trim to reasonable length
    return topic[:80], note[:120]


def load_db():
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {"items": [], "next_id": 1}


def save_db(db):
    DB_FILE.write_text(json.dumps(db, indent=2, default=str))


def main():
    # Get commit message
    commit_msg = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B"]
    ).decode().strip()

    # Skip non-learning commits
    for prefix in SKIP_PREFIXES:
        if commit_msg.startswith(prefix):
            print(f"[revision] Skipped (prefix: {prefix})")
            return

    # Get changed files
    changed = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"]
    ).decode().strip().splitlines()

    if not changed:
        return

    topic, note = parse_commit_message(commit_msg)
    category = detect_category(changed)
    file_ref = changed[0] if changed else None   # first changed file as reference

    # Build item
    today = date.today()
    revisions = [
        {"due": str(today + timedelta(days=d)), "done": False, "result": None}
        for d in SCHEDULE
    ]

    db = load_db()
    item = {
        "id":        db["next_id"],
        "topic":     topic,
        "category":  category,
        "note":      note,
        "file":      file_ref,
        "learned":   str(today),
        "revisions": revisions,
        "buried":    False
    }
    db["items"].append(item)
    db["next_id"] += 1
    save_db(db)

    print(f"[revision] ✅ Added: [{category}] {topic}")
    print(f"[revision]    Revise on: {', '.join(r['due'] for r in revisions)}")


if __name__ == "__main__":
    main()
