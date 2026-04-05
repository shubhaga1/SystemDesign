-- ============================================================
-- TIMING & SIDE-CHANNEL ATTACKS — and how to prevent them
-- Based on AWS session by Krantikaran Burada & Narendra Tawar
--
-- HOW IT WORKS:
--   Attacker uses query response TIME to infer secret data.
--   Faster = condition was false. Slower = condition was true + delay.
--   Binary search: guess one character at a time → O(log n) guesses.
--
-- Run: psql -h localhost -U admin -d learndb -f 03_timing_attacks.sql
-- ============================================================

-- ─── Setup ───────────────────────────────────────────────────
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS login_attempts;

CREATE TABLE patients (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100),
    blood_type VARCHAR(3),   -- sensitive — attacker wants to know
    secret_key VARCHAR(64)   -- simulates API key / password stored in DB
);

INSERT INTO patients (name, blood_type, secret_key) VALUES
    ('Alice', 'O+',  'sk_live_abc123secret'),
    ('Bob',   'AB-', 'sk_live_xyz789hidden'),
    ('Carol', 'A+',  'sk_live_pqr456private');

CREATE TABLE login_attempts (
    id         SERIAL PRIMARY KEY,
    username   VARCHAR(50),
    attempted_at TIMESTAMPTZ DEFAULT NOW(),
    success    BOOLEAN
);

-- ─── 1. VULNERABLE — timing attack on password guess ─────────
-- Attacker controls the WHERE clause input.
-- They measure response time to learn if condition is true.

-- Vulnerable pattern: string comparison leaks timing info
-- When condition is TRUE, pg_sleep adds delay → attacker detects it
-- This is what the attacker does (via SQL injection or direct access):

-- [ATTACKER QUERY] - detects if blood_type starts with 'O'
-- DO $$
-- BEGIN
--     IF (SELECT blood_type FROM patients WHERE id=1) LIKE 'O%' THEN
--         PERFORM pg_sleep(0.5);  -- measurable delay = 'yes, it starts with O'
--     END IF;
-- END $$;

-- Simulate what an attacker sees:
DO $$
DECLARE
    t1 TIMESTAMPTZ;
    t2 TIMESTAMPTZ;
    duration INTERVAL;
BEGIN
    -- Guess 1: does blood_type start with 'A'? (wrong)
    t1 := clock_timestamp();
    IF (SELECT blood_type FROM patients WHERE id = 1) LIKE 'A%' THEN
        PERFORM pg_sleep(0.3);
    END IF;
    t2 := clock_timestamp();
    duration := t2 - t1;
    RAISE NOTICE 'Guess A%%: duration = %  (fast = MISS)', duration;

    -- Guess 2: does blood_type start with 'O'? (correct)
    t1 := clock_timestamp();
    IF (SELECT blood_type FROM patients WHERE id = 1) LIKE 'O%' THEN
        PERFORM pg_sleep(0.3);
    END IF;
    t2 := clock_timestamp();
    duration := t2 - t1;
    RAISE NOTICE 'Guess O%%: duration = %  (slow = HIT — blood type starts with O!)', duration;
END $$;

-- ─── 2. VULNERABLE — pg_statistic side-channel ───────────────
-- January 2026 incident: pg_statistic stores column statistics
-- An attacker with SELECT on pg_statistic can infer data distribution
-- without reading the actual table

-- pg_statistic stores: most common values, frequencies, histograms
-- Visible to any user by default in older PostgreSQL versions

-- Check what stats are stored (run as admin to see):
SELECT attname, stakind1, stavalues1
FROM   pg_statistic s
JOIN   pg_attribute a ON s.starelid = a.attrelid AND s.staattnum = a.attnum
WHERE  s.starelid = 'patients'::regclass;

-- ─── 3. VULNERABLE — hardcoded secret in query ────────────────
-- Attacker injects into query that has secret hardcoded
-- Query log reveals the secret

-- BAD: secret in query string
-- SELECT * FROM patients WHERE secret_key = 'sk_live_abc123secret';
-- → appears in pg_stat_activity, pg_log, slow query log

-- ─── 4. FIX — Parameterized queries ──────────────────────────
-- Parameterized queries separate code from data
-- Secret never appears in query text

-- In application code (pseudocode):
/*
  // Java / JDBC — parameterized
  PreparedStatement stmt = conn.prepareStatement(
      "SELECT * FROM patients WHERE secret_key = ?"
  );
  stmt.setString(1, userInput);   // data goes through parameter, not query string
  ResultSet rs = stmt.executeQuery();

  // Node.js / pg
  const result = await client.query(
      'SELECT * FROM patients WHERE secret_key = $1',
      [userInput]
  );

  // Python / psycopg2
  cursor.execute("SELECT * FROM patients WHERE secret_key = %s", (user_input,))
*/

-- In pure SQL — use PREPARE for repeated queries
PREPARE find_patient (VARCHAR) AS
    SELECT id, name FROM patients WHERE secret_key = $1;

-- Execute with parameter — secret not in query text
EXECUTE find_patient('sk_live_abc123secret');

DEALLOCATE find_patient;

-- ─── 5. FIX — Rate limiting login attempts ────────────────────
-- Detect brute-force / timing attacks via abnormal query volume

-- Track failed logins
CREATE OR REPLACE FUNCTION record_login(p_username VARCHAR, p_success BOOLEAN)
RETURNS VOID AS $$
BEGIN
    INSERT INTO login_attempts (username, success) VALUES (p_username, p_success);
END;
$$ LANGUAGE plpgsql;

-- Detect brute force: > 5 failures in 10 minutes
CREATE OR REPLACE VIEW suspicious_logins AS
SELECT
    username,
    COUNT(*)                           AS failed_attempts,
    MIN(attempted_at)                  AS first_attempt,
    MAX(attempted_at)                  AS last_attempt,
    MAX(attempted_at) - MIN(attempted_at) AS window
FROM   login_attempts
WHERE  success = FALSE
  AND  attempted_at > NOW() - INTERVAL '10 minutes'
GROUP  BY username
HAVING COUNT(*) > 5;

-- Simulate some failed logins
SELECT record_login('attacker', FALSE);
SELECT record_login('attacker', FALSE);
SELECT record_login('attacker', FALSE);
SELECT record_login('attacker', FALSE);
SELECT record_login('attacker', FALSE);
SELECT record_login('attacker', FALSE);

SELECT * FROM suspicious_logins;

-- ─── 6. FIX — Revoke pg_statistic access ──────────────────────
-- In PG 14+, pg_stats_ext visible to table owners only
-- Restrict access to statistics for sensitive tables:

REVOKE SELECT ON pg_statistic FROM PUBLIC;
-- Requires superuser; use pg_stats view which enforces table ownership check

-- ─── Summary ─────────────────────────────────────────────────
/*
  TIMING ATTACK DEFENSES:
  1. Never put secrets in query strings  → use parameterized queries
  2. Never SELECT sensitive columns into conditions  → application-level check
  3. Rate limit login attempts  → view + monitoring on login_attempts
  4. Revoke pg_statistic from public  → hides column statistics
  5. Use constant-time comparison for passwords  → pgcrypto extension
  6. Monitor pg_stat_activity for abnormal patterns
*/
