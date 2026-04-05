-- ============================================================
-- LOGICAL REPLICATION — setup, security, vulnerabilities
-- Based on AWS session — replication slot abuse & malicious dumps
--
-- USE CASES:
--   - Zero-downtime major version upgrades
--   - Real-time data lake / warehouse feeding
--   - Cross-region replication
--   - Blue-green deployments
--
-- HOW IT WORKS:
--   Publisher writes changes to WAL (Write-Ahead Log)
--   → Logical Replication Slot decodes WAL to SQL changes
--   → Subscriber applies changes on its side
--
-- Run: psql -h localhost -U admin -d learndb -f 05_logical_replication.sql
-- ============================================================

-- ─── 1. Enable logical replication ───────────────────────────
-- Requires: wal_level = logical in postgresql.conf
-- Check current setting:
SHOW wal_level;  -- must be 'logical' for replication

-- Set in postgresql.conf (requires restart):
-- wal_level = logical
-- max_replication_slots = 10
-- max_wal_senders = 10

-- ─── 2. Create a dedicated replication user ───────────────────
-- NEVER use superuser for replication (AWS session key point)
-- Use least-privilege replication role

DROP ROLE IF EXISTS replicator;
CREATE ROLE replicator
    LOGIN
    REPLICATION                        -- replication privilege only
    PASSWORD 'rep_strong_pass_123!'
    CONNECTION LIMIT 5;                -- limit concurrent connections

-- Grant read access to the tables we want to replicate
GRANT SELECT ON ALL TABLES IN SCHEMA public TO replicator;

-- ─── 3. Create publication (on publisher / primary) ───────────
-- Publication = what to replicate

-- Replicate specific tables only (not everything — least privilege)
CREATE PUBLICATION my_pub
    FOR TABLE users, orders
    WITH (publish = 'insert, update, delete');  -- not truncate

-- See existing publications:
SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete
FROM   pg_publication;

-- ─── 4. Replication slots — the dangerous part ────────────────
-- Slot holds WAL until subscriber confirms receipt
-- DANGER: abandoned slot = WAL accumulates = disk full = DB crash

-- Create a logical replication slot
SELECT pg_create_logical_replication_slot('my_slot', 'pgoutput');

-- See all slots and their lag:
SELECT
    slot_name,
    slot_type,
    active,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS lag_behind,
    wal_status
FROM pg_replication_slots;

-- ─── 5. DANGER — abandoned slot causes disk exhaustion ────────
-- If subscriber disconnects and never resumes:
--   WAL keeps accumulating → disk fills → DB crashes
--   Attacker can deliberately disconnect to cause DoS

-- Monitor: alert if slot lag > threshold (e.g., 1GB)
CREATE OR REPLACE VIEW replication_slot_health AS
SELECT
    slot_name,
    active,
    pg_size_pretty(
        pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)
    )                       AS wal_lag,
    pg_wal_lsn_diff(
        pg_current_wal_lsn(), restart_lsn
    )                       AS wal_lag_bytes,
    CASE
        WHEN NOT active AND
             pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) > 1073741824
        THEN 'DANGER — drop this slot!'
        WHEN NOT active THEN 'WARNING — inactive slot'
        ELSE 'OK'
    END                     AS health_status
FROM pg_replication_slots;

SELECT * FROM replication_slot_health;

-- Drop a slot that's no longer needed (cleanup)
-- SELECT pg_drop_replication_slot('my_slot');

-- ─── 6. ATTACK — malicious metadata in pg_dump ────────────────
-- From AWS session: attacker embeds malicious command in pg_dump metadata
-- When restored on subscriber, command executes in DB context

-- EXAMPLE of what attacker does (metadata-only dump):
-- pg_dump --schema-only -f backup.sql mydb
-- Then inserts into backup.sql:
--   COMMENT ON TABLE public.users IS ''; SELECT pg_read_file('pg_hba.conf');--

-- DEFENSE: Use binary format (not text)
--   pg_dump -Fc -f backup.dump mydb      ← binary format, injection impossible
--   pg_restore -d mydb backup.dump

-- ALSO: Verify dump checksums before restore
--   pg_dump --no-comments ...            ← strip comments that could hide code

-- ─── 7. DEFENSE: pg_hba.conf for replication ─────────────────
-- Restrict which hosts can connect for replication
/*
  # pg_hba.conf entries for replication (on publisher):
  TYPE   DATABASE    USER         ADDRESS          METHOD
  host   replication replicator   10.0.1.0/24      scram-sha-256
  host   replication replicator   subscriber_ip/32  scram-sha-256

  # Block all other replication connections:
  host   replication all          0.0.0.0/0        reject
*/

-- ─── 8. Monitor active replication connections ────────────────
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    sync_state
FROM pg_stat_replication;

-- ─── Summary ─────────────────────────────────────────────────
/*
  LOGICAL REPLICATION SECURITY:
  1. Dedicated replication role with REPLICATION privilege only
     → never use postgres superuser

  2. pg_hba.conf allow-list for replication connections
     → only specific IPs, reject all others

  3. Monitor pg_replication_slots for:
     → inactive slots with high lag = DoS risk = drop them
     → alert if lag > 1GB

  4. Use binary pg_dump format (-Fc)
     → prevents command injection in metadata

  5. Specific publication tables (not FOR ALL TABLES)
     → only replicate what subscriber needs

  6. Verify dump integrity with checksums before restore
*/
