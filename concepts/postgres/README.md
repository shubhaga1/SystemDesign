# PostgreSQL — Concepts, Security & Performance

Runnable SQL POCs covering core Postgres usage + security threats from the AWS session by Krantikaran Burada & Narendra Tawar.

---

## Quick start

```bash
# Start Postgres
docker-compose up -d

# Connect
psql -h localhost -U admin -d learndb

# Run any file
psql -h localhost -U admin -d learndb -f 01_basics.sql
```

---

## Files — learning order

| # | File | Covers |
| --- | --- | --- |
| 1 | `01_basics.sql` | DDL, DML, JOINs, aggregates, window functions, CTEs, indexes |
| 2 | `07_window_functions.sql` | RANK, DENSE_RANK, LAG, LEAD, COALESCE, NULLIF, CASE, STRING_AGG, FILTER |
| 3 | `06_performance.sql` | EXPLAIN, index types, VACUUM, partitioning, JSONB |
| 4 | `02_roles_and_privileges.sql` | Role creation, least privilege, inheritance pitfalls, RLS |
| 5 | `03_timing_attacks.sql` | Side-channel attacks, parameterized queries, rate limiting |
| 6 | `04_extensions_security.sql` | Privilege escalation via extensions, search_path, pgaudit |
| 7 | `05_logical_replication.sql` | Replication slots, dedicated users, pg_hba.conf, slot monitoring |

---

## Key Functions Reference

### Ranking
```sql
RANK()        OVER (PARTITION BY dept ORDER BY salary DESC)  -- 1,1,3 (gaps after tie)
DENSE_RANK()  OVER (PARTITION BY dept ORDER BY salary DESC)  -- 1,1,2 (no gaps)
ROW_NUMBER()  OVER (PARTITION BY dept ORDER BY salary DESC)  -- 1,2,3 (always unique)
NTILE(4)      OVER (ORDER BY salary DESC)                    -- quartiles
```

### Lag / Lead
```sql
LAG(revenue)  OVER (PARTITION BY emp_id ORDER BY month)  -- previous row value
LEAD(revenue) OVER (PARTITION BY emp_id ORDER BY month)  -- next row value
```

### Null handling
```sql
COALESCE(a, b, c)     -- first non-null: COALESCE(discount, 0)
NULLIF(a, b)          -- return NULL if a=b: prevent divide-by-zero NULLIF(count, 0)
```

### Conditional
```sql
CASE WHEN salary > 90000 THEN 'Senior' ELSE 'Junior' END
COUNT(*) FILTER (WHERE salary > 80000)   -- conditional aggregate
```

### Grouping helpers
```sql
STRING_AGG(name, ', ' ORDER BY name)     -- join names into one string
ARRAY_AGG(salary ORDER BY salary DESC)  -- collect into array
GREATEST(a, b, c)   -- max of multiple values
LEAST(a, b, c)      -- min of multiple values
```

---

## Security threats (AWS session)

### 1. Privilege escalation via extensions
```sql
-- Attacker plants malicious function in public schema
-- Superuser installs extension → search_path hits public first → code executes

-- DEFENSE:
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
ALTER ROLE app_user SET search_path = pg_catalog, myschema;
```

### 2. Timing / side-channel attacks
```sql
-- Attacker uses pg_sleep() delays to infer column values character by character

-- DEFENSE: parameterized queries
PREPARE find_user (VARCHAR) AS SELECT * FROM users WHERE secret = $1;
EXECUTE find_user('input');
```

### 3. Logical replication slot abuse
```sql
-- Abandoned slot → WAL accumulates → disk full → crash

-- DEFENSE: monitor slot lag
SELECT slot_name, pg_size_pretty(
    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag
FROM pg_replication_slots;
```

### 4. Role inheritance pitfalls
```sql
-- Complex chains: A inherits B inherits C → unintended privilege escalation

-- DEFENSE:
CREATE ROLE admin_ops NOINHERIT;  -- must SET ROLE explicitly
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
```

---

## Security hardening checklist

```sql
-- 1. Revoke public schema create
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- 2. Dedicated app role, not superuser
CREATE ROLE app_user LOGIN PASSWORD '...' NOINHERIT;
GRANT SELECT, INSERT, UPDATE ON specific_tables TO app_user;

-- 3. Parameterized queries everywhere (in application code)
-- Never string-concatenate user input into SQL

-- 4. Monitor replication slots
-- Alert if inactive slot with lag > 1GB

-- 5. Restrict extension creation to superusers (default — don't change)

-- 6. Enable pgaudit for comprehensive logging
-- shared_preload_libraries = 'pgaudit'
-- pgaudit.log = 'ddl, role, read, write'

-- 7. Password rotation
ALTER ROLE app_user VALID UNTIL '2026-12-31';
```
