#!/usr/bin/env python3
"""
REVISION SYSTEM — Spaced Repetition Auto-Scheduler

Usage:
  python revise.py              → show what to revise TODAY
  python revise.py add          → log something you just learned
  python revise.py done <id>    → mark done ✅ (confident)
  python revise.py weak <id>    → mark weak ❌ (re-schedules from today)
  python revise.py all          → show full log
  python revise.py review       → ask Claude to audit today's output

How it works:
  Every git commit → hook auto-adds topic to DB.
  Scheduled: D+1, D+3, D+7 from learned date.
  Daily: run `python revise.py` → see ONLY today's items.
  Mark done ✅ or weak ❌ (reschedules again from today).

No manual tracking. Fully automatic via git hooks.
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

def short_file(path):
    """Show only the filename, not the full path."""
    return Path(path).name if path else ""

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
        print(f"\n✅ Nothing due today ({today}). Keep learning!")
        return

    overdue = [(i, r_i, r) for i, r_i, r in due if r["due"] < today]
    today_due = [(i, r_i, r) for i, r_i, r in due if r["due"] == today]

    print(f"\n{'━'*52}")
    print(f"  REVISE — {today}  ({len(due)} items: {len(overdue)} overdue)")
    print(f"{'━'*52}")

    def print_section(items, label):
        if not items:
            return
        print(f"\n  {label}")
        by_cat = {}
        for item, rev_idx, rev in items:
            by_cat.setdefault(item["category"], []).append((item, rev_idx, rev))
        for cat, cat_items in by_cat.items():
            print(f"  ┌─ {cat}")
            for item, rev_idx, rev in cat_items:
                fname = short_file(item["file"])
                print(f"  │  [{item['id']:2d}] {item['topic']}")
                print(f"  │       💡 {item['note'][:70]}")
                if fname:
                    print(f"  │       📄 {fname}")
            print(f"  └{'─'*48}")

    print_section(overdue,   "⚠️  OVERDUE")
    print_section(today_due, "📅  TODAY")

    print(f"\n  done <id>  ✅  weak <id>  ❌\n")

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

def review_with_claude(db):
    """Run Claude on today's revision output to check clarity and suggest improvements."""
    import subprocess, io
    from contextlib import redirect_stdout

    # Capture today's output
    buf = io.StringIO()
    with redirect_stdout(buf):
        show_today(db)
    output = buf.getvalue()

    prompt = f"""You are reviewing a spaced repetition learning output for a senior engineer.

Here is what they need to revise today:

{output}

Please:
1. Flag any topics whose KEY INSIGHT (💡) is too vague or hard to recall from
2. Suggest a sharper one-liner for those (max 80 chars)
3. Note if any topic title is unclear
4. Give an overall ease-of-learning score (1-5) with one reason

Be concise. No bullet spam."""

    print("\n🤖 Asking Claude to review your revision output...\n")
    subprocess.run(["claude", "-p", prompt], check=True)

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
    elif args[0] == "review":
        review_with_claude(db)
    else:
        print(__doc__)
