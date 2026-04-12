#!/usr/bin/env python3
"""
Called by git post-commit hook automatically.
Reads commit message + changed files → adds to revision DB.

Auto-detects category from:
  1. The repo name (e.g. 'algorithms' → DSA)
  2. The subfolder path (e.g. 'queue/' → DSA-Queue)

Works for ANY repo under /Users/shubhamgarg/Downloads/Code/
No need to register repos — just install the hook.

Commit message format:
  Add <Topic> — <Key insight one line>
  Example: Add BFS level order — snapshot queue.size() before for loop

Skip if message starts with:
  fix: / chore: / merge / Merge / wip / WIP / Add revision / seed
"""

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

REVISION_DIR = Path("/Users/shubhamgarg/Downloads/Code/SystemDesign/revision")
DB_FILE      = REVISION_DIR / "revision_db.json"
SCHEDULE     = [1, 3, 7]

# ── Category detection ────────────────────────────────────────────────────────
# Checked in order — first match wins.
# Pattern matched against full file path (repo/subfolder/file).
# More specific patterns must come BEFORE generic ones.

CATEGORY_MAP = [
    # DSA subfolders
    ("queue",           "DSA-Queue"),
    ("tree",            "DSA-Tree"),
    ("stack",           "DSA-Stack"),
    ("array",           "DSA-Array"),
    ("sorting",         "DSA-Sorting"),
    ("graph",           "DSA-Graph"),
    ("recursion",       "DSA-Recursion"),
    ("hashmap",         "DSA-HashMap"),
    ("slidingWindow",   "DSA-SlidingWindow"),
    ("linkedList",      "DSA-LinkedList"),
    ("LinkedList",      "DSA-LinkedList"),
    ("searching",       "DSA-Searching"),
    ("dynamic",         "DSA-DP"),
    ("dp",              "DSA-DP"),
    # Languages / Java
    ("java8",           "Java"),
    ("fundamentals",    "Java"),
    ("java",            "Java"),
    # System design topics
    ("encryption",      "Encryption"),
    ("sql",             "SQL"),
    ("spark",           "SystemDesign"),
    ("system-design",   "SystemDesign"),
    ("in-memory",       "SystemDesign"),
    ("spatial",         "SystemDesign"),
    ("postgres",        "SQL"),
    # Infra
    ("kafka",           "Kafka"),
    ("docker",          "K8s"),
    ("k8s",             "K8s"),
    ("kubernetes",      "K8s"),
    # ML / AI
    ("huggingface",     "ML"),
    ("langchain",       "ML"),
    ("langsmith",       "ML"),
    ("vllm",            "ML"),
    ("vector-db",       "ML"),
    ("nvidia",          "ML"),
    ("nemo",            "ML"),
    ("mcp",             "ML"),
    # Other
    ("git",             "Git"),
    ("python",          "Python"),
    ("investment",      "Finance"),
    ("aem",             "AEM"),
    ("aws",             "Cloud"),
    # Repo-level fallbacks (matched on repo name in path)
    ("algorithms",      "DSA"),
    ("learning-journal","Learning"),
    ("SystemDesign",    "SystemDesign"),
]

SKIP_PREFIXES = [
    "fix:", "chore:", "merge", "Merge", "wip", "WIP",
    "Add revision", "Update revision", "Seed", "seed",
    "Update .gitignore", "Move ", "Rename ",
]


def detect_category(changed_files: list[str], repo_root: str) -> str:
    """
    Detect category from file paths.
    Tries subfolder match first, then falls back to repo name.
    """
    # Use repo root name as context too
    repo_name = Path(repo_root).name   # e.g. "algorithms", "learning-journal"
    all_paths = [f"{repo_name}/{f}" for f in changed_files]

    for path in all_paths:
        for pattern, category in CATEGORY_MAP:
            if pattern.lower() in path.lower():
                return category
    return "General"


def parse_commit_message(msg: str) -> tuple[str, str]:
    """
    Extract topic and note from commit message.

    'Add BFS level order — snapshot queue.size() before for loop'
    → topic: 'BFS level order'
    → note:  'snapshot queue.size() before for loop'
    """
    msg = msg.strip()

    # Strip common verb prefixes
    for prefix in ["Add ", "Update ", "Create ", "Implement ", "Refactor ", "Fix "]:
        if msg.startswith(prefix):
            msg = msg[len(prefix):]
            break

    # Split on em dash (—) or double dash (--)
    for sep in [" — ", " -- "]:
        if sep in msg:
            parts = msg.split(sep, 1)
            return parts[0].strip()[:80], parts[1].strip()[:120]

    # No separator — use full message as both
    return msg[:80], msg[:120]


def load_db() -> dict:
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {"items": [], "next_id": 1}


def save_db(db: dict):
    DB_FILE.write_text(json.dumps(db, indent=2, default=str))


def main():
    # ── Get commit message ────────────────────────────────────────────────────
    commit_msg = subprocess.check_output(
        ["git", "log", "-1", "--pretty=%B"]
    ).decode().strip()

    # ── Skip non-learning commits ─────────────────────────────────────────────
    for prefix in SKIP_PREFIXES:
        if commit_msg.startswith(prefix):
            print(f"[revision] Skipped")
            return

    # ── Get changed files and repo root ──────────────────────────────────────
    changed = subprocess.check_output(
        ["git", "diff-tree", "--no-commit-id", "-r", "--name-only", "HEAD"]
    ).decode().strip().splitlines()

    if not changed:
        return

    repo_root = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"]
    ).decode().strip()

    # ── Parse and categorize ──────────────────────────────────────────────────
    topic, note = parse_commit_message(commit_msg)
    category    = detect_category(changed, repo_root)
    file_ref    = f"{Path(repo_root).name}/{changed[0]}"  # repo/subfolder/file.java

    # ── Build revision item ───────────────────────────────────────────────────
    today = date.today()
    revisions = [
        {"due": str(today + timedelta(days=d)), "done": False, "result": None}
        for d in SCHEDULE
    ]

    db   = load_db()
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
