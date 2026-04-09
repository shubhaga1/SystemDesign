# SQL — Learning with SQLite

## What is SQLite?

SQLite is a database built into macOS by default — nothing to install.

```bash
which sqlite3
# /usr/bin/sqlite3  ← Apple ships it, always there
```

Apple uses it internally for Contacts, Calendar, Safari history, iMessage, Photos, Keychain.
It's the most widely deployed database in the world — every iPhone, Mac, and browser has it.

---

## SQLite vs Postgres

```
SQLite:
  Built into macOS — no install, no Docker, no server
  One file (or :memory:) = the entire database
  Good for: learning SQL, offline work, small apps
  Bad for:  multi-user, production, Postgres-specific features

Postgres:
  Full database server — needs Docker or install
  Good for: production, concurrent users, advanced features
  Supports: RANK, EXPLAIN, RLS, JSONB, replication, extensions
```

---

## How to run SQL files

### Option 1 — In-memory (wiped after run, good for testing)

```bash
./run_sql.sh 01_basics.sql
```

Uses `:memory:` — database exists only while the script runs, then gone.

```bash
# What run_sql.sh does internally:
sqlite3 :memory: < 01_basics.sql

# sqlite3    = the SQLite program
# :memory:   = don't create a file, use RAM only
# < file.sql = feed the SQL file as input (like typing it manually)
```

### Option 2 — Persistent file (stays, queryable after)

```bash
# Create a .db file from SQL
sqlite3 learn.db < 01_basics.sql

# Now open it interactively
sqlite3 learn.db
```

Use this when you want to query the data after the script runs.

---

## Interactive SQLite shell — useful commands

```bash
# Open a database
sqlite3 learn.db

# Inside the shell:
.tables              # list all tables
.schema emp          # show CREATE TABLE for emp
.headers on          # show column names in output
.mode column         # pretty column alignment
.quit                # exit (also: Ctrl+D)

# Run any SQL — ALWAYS end with semicolon
SELECT * FROM emp;
SELECT * FROM emp WHERE salary > 80000;
SELECT department, AVG(salary) FROM emp GROUP BY department;
```

**Why semicolon matters:**
```
sqlite> select * from emp       ← no semicolon
   ...>                         ← waiting, thinks query isn't done
sqlite> select * from emp;      ← semicolon = "I'm done, run it"
```

---

## Why :memory: vs .db file

```
:memory:          → in-memory, wiped when script ends
                    use when: just want to see query output, no persistence needed
                    run_sql.sh uses this by default

learn.db          → file on disk, persists forever
                    use when: want to open sqlite3 and explore data interactively
                    create with: sqlite3 learn.db < file.sql
```

---

## How $1 and < work in the run script

```bash
./run_sql.sh 01_basics.sql
              ↑
              $1 = first argument = "01_basics.sql"
              $2 = second argument (if any)
              $0 = the script name itself
```

```bash
if [ -z "$FILE" ]; then   # -z = "is this string empty?"
    echo "Usage..."
    exit 1                # exit 1 = error (0 = success)
fi

sqlite3 :memory: < "$FILE"
#                ↑
#                < = redirect file contents as input to sqlite3
#                (same as typing the SQL manually inside sqlite3)
```

---

## Files

| File | Covers |
| --- | --- |
| `01_basics.sql` | WHERE vs HAVING, GROUP BY, execution order, emp table |
| `run_sql.sh` | Runner — targets SQLite in-memory |

---

## Quick start

```bash
# Run and see output
./run_sql.sh 01_basics.sql

# Run and keep data to explore
sqlite3 learn.db < 01_basics.sql
sqlite3 learn.db
.tables
select * from emp;
.quit
```
