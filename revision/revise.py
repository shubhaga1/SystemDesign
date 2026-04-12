#!/usr/bin/env python3
"""
REVISION SYSTEM — Spaced Repetition Auto-Scheduler

Usage:
  python revise.py              → show what to revise TODAY
  python revise.py add          → log something you just learned
  python revise.py done <id>    → mark a revision done (✅ confident)
  python revise.py weak <id>    → mark weak (❌ re-schedule from today)
  python revise.py all          → show full revision log

How it works:
  When you learn something → run `python revise.py add`
  It auto-schedules: D+1, D+3, D+7 from today.
  Each day: run `python revise.py` → see ONLY today's items.
  Mark done (✅) or weak (❌ → reschedules again from today).

No manual date tracking. Fully automatic.
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path

DB_FILE = Path(__file__).parent / "revision_db.json"

SCHEDULE = [1, 3, 7]   # D+1, D+3, D+7 from learn date

# ── DB helpers ────────────────────────────────────────────────────────────────

def load_db():
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text())
    return {"items": [], "next_id": 1}

def save_db(db):
    DB_FILE.write_text(json.dumps(db, indent=2, default=str))

# ── Core logic ────────────────────────────────────────────────────────────────

def add_item(db):
    print("\n── Add New Learning Entry ──────────────────")
    topic    = input("Topic (e.g. 'BFS level order'): ").strip()
    category = input("Category (DSA / SystemDesign / SQL / Kafka / K8s / Python / Encryption): ").strip()
    note     = input("Key insight (one line): ").strip()
    file_ref = input("File (e.g. algorithms/queue/01_QueueBasics.java) [Enter to skip]: ").strip()

    learned_date = date.today()
    revisions = [
        {"due": str(learned_date + timedelta(days=d)), "done": False, "result": None}
        for d in SCHEDULE
    ]

    item = {
        "id":          db["next_id"],
        "topic":       topic,
        "category":    category,
        "note":        note,
        "file":        file_ref or None,
        "learned":     str(learned_date),
        "revisions":   revisions,
        "buried":      False
    }
    db["items"].append(item)
    db["next_id"] += 1
    save_db(db)

    print(f"\n✅ Added! Scheduled for revision on:")
    for r in revisions:
        print(f"   {r['due']}")

def show_today(db):
    today = str(date.today())
    due = []

    for item in db["items"]:
        if item["buried"]:
            continue
        for i, rev in enumerate(item["revisions"]):
            if not rev["done"] and rev["due"] <= today:
                due.append((item, i, rev))

    if not due:
        print(f"\n🎉 Nothing due today ({today}). Keep learning!")
        return

    print(f"\n{'='*60}")
    print(f"  REVISE TODAY — {today}  ({len(due)} items)")
    print(f"{'='*60}")

    by_category = {}
    for item, rev_idx, rev in due:
        cat = item["category"]
        by_category.setdefault(cat, []).append((item, rev_idx, rev))

    for cat, items in by_category.items():
        print(f"\n  [{cat}]")
        for item, rev_idx, rev in items:
            overdue = " ⚠️ OVERDUE" if rev["due"] < today else ""
            rev_num = SCHEDULE[rev_idx]
            print(f"    ID={item['id']}  D+{rev_num:<2}  {item['topic']}")
            print(f"           💡 {item['note']}")
            if item["file"]:
                print(f"           📄 {item['file']}")
            print(f"           Due: {rev['due']}{overdue}")

    print(f"\n{'─'*60}")
    print("  Commands:")
    print("    python revise.py done <id>   → ✅ confident, mark complete")
    print("    python revise.py weak <id>   → ❌ forgot, re-schedule from today")
    print(f"{'─'*60}")

def mark_done(db, item_id):
    today = str(date.today())
    item = next((i for i in db["items"] if i["id"] == item_id), None)
    if not item:
        print(f"ID {item_id} not found.")
        return

    # Find the next pending revision
    for rev in item["revisions"]:
        if not rev["done"] and rev["due"] <= today:
            rev["done"] = True
            rev["result"] = "✅"
            save_db(db)
            print(f"✅ Marked done: {item['topic']}")

            # Check if all revisions complete
            if all(r["done"] for r in item["revisions"]):
                print(f"   🎓 All revisions complete! Topic mastered.")
            else:
                next_rev = next((r for r in item["revisions"] if not r["done"]), None)
                if next_rev:
                    print(f"   Next revision: {next_rev['due']}")
            return

    print(f"No pending revision due today for ID {item_id}.")

def mark_weak(db, item_id):
    today = date.today()
    item = next((i for i in db["items"] if i["id"] == item_id), None)
    if not item:
        print(f"ID {item_id} not found.")
        return

    # Mark current as done (with ❌) and re-schedule all from today
    for rev in item["revisions"]:
        if not rev["done"] and rev["due"] <= str(today):
            rev["done"] = True
            rev["result"] = "❌"
            break

    # Add fresh revision cycle from today
    new_revisions = [
        {"due": str(today + timedelta(days=d)), "done": False, "result": None}
        for d in SCHEDULE
    ]
    item["revisions"].extend(new_revisions)
    save_db(db)
    print(f"❌ Marked weak: {item['topic']}")
    print(f"   Re-scheduled: {[r['due'] for r in new_revisions]}")

def show_all(db):
    print(f"\n{'='*60}")
    print(f"  ALL REVISION ITEMS ({len(db['items'])} total)")
    print(f"{'='*60}")

    today = str(date.today())
    for item in db["items"]:
        if item["buried"]:
            continue
        pending = [r for r in item["revisions"] if not r["done"]]
        done    = [r for r in item["revisions"] if r["done"]]
        status  = "✅ Mastered" if not pending else f"Next: {pending[0]['due']}"
        overdue = " ⚠️" if pending and pending[0]["due"] < today else ""

        print(f"\n  ID={item['id']} [{item['category']}] {item['topic']}")
        print(f"    Learned: {item['learned']}  |  {status}{overdue}")
        print(f"    💡 {item['note']}")
        results = [r.get("result", "⏳") or "⏳" for r in item["revisions"]]
        print(f"    Revisions: {' → '.join(results)}")

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db = load_db()
    args = sys.argv[1:]

    if not args:
        show_today(db)
    elif args[0] == "add":
        add_item(db)
    elif args[0] == "done" and len(args) == 2:
        mark_done(db, int(args[1]))
    elif args[0] == "weak" and len(args) == 2:
        mark_weak(db, int(args[1]))
    elif args[0] == "all":
        show_all(db)
    else:
        print(__doc__)
