-- ============================================================
-- PERFORMANCE — EXPLAIN, indexes, query tuning
-- Run: psql -h localhost -U admin -d learndb -f 06_performance.sql
-- ============================================================

-- ─── 1. EXPLAIN — understand query plan ──────────────────────
-- EXPLAIN: show plan without running
-- EXPLAIN ANALYZE: run + show actual timings
-- EXPLAIN (ANALYZE, BUFFERS): also show cache hits/misses

EXPLAIN SELECT * FROM users WHERE email = 'alice@example.com';
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'alice@example.com';

-- ─── 2. Index types ───────────────────────────────────────────
-- B-Tree (default): =, <, >, BETWEEN, ORDER BY, LIKE 'prefix%'
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Partial index: only index subset of rows (saves space, faster)
-- e.g., only index active users — inactive users never searched
CREATE INDEX IF NOT EXISTS idx_users_active_email
    ON users(email)
    WHERE is_active = TRUE;

-- Composite index: multiple columns — order matters!
-- Useful for queries that filter/sort on both columns together
CREATE INDEX IF NOT EXISTS idx_orders_user_status
    ON orders(user_id, status);
-- Covers:  WHERE user_id = 1 AND status = 'shipped'
-- Covers:  WHERE user_id = 1  (left-prefix works)
-- MISSES:  WHERE status = 'shipped'  (right column alone doesn't use index)

-- Covering index: include extra columns to avoid table lookup
CREATE INDEX IF NOT EXISTS idx_orders_covering
    ON orders(user_id)
    INCLUDE (product, amount);  -- query only needs these → index-only scan

-- ─── 3. pg_stat_statements — find slow queries ────────────────
-- Requires: shared_preload_libraries = 'pg_stat_statements' in postgresql.conf
-- CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 slowest queries:
/*
SELECT
    round(mean_exec_time::numeric, 2) AS avg_ms,
    calls,
    round(total_exec_time::numeric, 2) AS total_ms,
    LEFT(query, 80) AS query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
*/

-- ─── 4. VACUUM and ANALYZE ────────────────────────────────────
-- VACUUM: reclaim space from dead rows (after UPDATE/DELETE)
-- ANALYZE: update statistics so planner makes good decisions
-- AUTOVACUUM: PostgreSQL does this automatically, but you can force it

VACUUM ANALYZE users;
VACUUM ANALYZE orders;

-- VACUUM FULL: locks table, rewrites it — only when very bloated
-- VACUUM FULL orders;

-- Check table bloat:
SELECT
    schemaname,
    tablename,
    n_live_tup   AS live_rows,
    n_dead_tup   AS dead_rows,
    last_autovacuum,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;

-- ─── 5. Connection pooling concept ────────────────────────────
-- PostgreSQL creates one OS process per connection (expensive)
-- At 1000 connections: 1GB+ RAM just for connection overhead
-- Solution: PgBouncer sits between app and DB, reuses connections

/*
  WITHOUT POOLING:
    App (1000 threads) → 1000 DB connections → 1000 OS processes

  WITH PGBOUNCER:
    App (1000 threads) → PgBouncer → 20 DB connections → 20 OS processes

  Modes:
    session:     connection held for entire session  (safe for all features)
    transaction: connection released after each txn (most efficient)
    statement:   connection released after each stmt (limited feature support)
*/

-- ─── 6. Partitioning — for very large tables ──────────────────
-- Split a large table into smaller physical pieces
-- Queries on a specific range only scan relevant partition

DROP TABLE IF EXISTS events CASCADE;

CREATE TABLE events (
    id         BIGSERIAL,
    user_id    INTEGER NOT NULL,
    event_type VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);    -- partition by date

-- Create monthly partitions
CREATE TABLE events_2026_01 PARTITION OF events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE events_2026_02 PARTITION OF events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE events_2026_03 PARTITION OF events
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- Insert goes to correct partition automatically
INSERT INTO events (user_id, event_type, created_at) VALUES
    (1, 'login',   '2026-01-15'),
    (2, 'purchase','2026-02-20'),
    (1, 'logout',  '2026-03-05');

-- Query on date range = only scans relevant partition (partition pruning)
EXPLAIN SELECT * FROM events WHERE created_at >= '2026-02-01' AND created_at < '2026-03-01';

-- ─── 7. JSONB — flexible schema inside PostgreSQL ─────────────
DROP TABLE IF EXISTS events_flex;

CREATE TABLE events_flex (
    id         SERIAL PRIMARY KEY,
    event_type VARCHAR(50),
    payload    JSONB,          -- binary JSON — indexable, queryable
    created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO events_flex (event_type, payload) VALUES
    ('purchase', '{"product":"MacBook","amount":2499,"currency":"USD","promo":"SAVE10"}'),
    ('login',    '{"ip":"192.168.1.1","device":"iPhone","os":"iOS 17"}'),
    ('error',    '{"code":500,"message":"DB timeout","retry":true}');

-- Query JSONB with -> (returns JSON) and ->> (returns text)
SELECT
    event_type,
    payload->>'product'            AS product,
    (payload->>'amount')::NUMERIC  AS amount,
    payload->'currency'            AS currency_json,  -- returns "USD" (JSON string)
    payload->>'currency'           AS currency_text   -- returns USD  (text)
FROM events_flex
WHERE event_type = 'purchase';

-- Filter inside JSONB
SELECT * FROM events_flex WHERE payload->>'code' = '500';
SELECT * FROM events_flex WHERE (payload->>'amount')::NUMERIC > 1000;

-- GIN index on JSONB — makes @> (contains) and key queries fast
CREATE INDEX idx_events_payload ON events_flex USING GIN (payload);

-- @> operator: does payload CONTAIN this JSON?
SELECT * FROM events_flex WHERE payload @> '{"event_type":"purchase"}';
