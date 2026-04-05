-- ============================================================
-- ROLES & PRIVILEGES — PostgreSQL access control
-- Based on AWS session: role inheritance pitfalls + least privilege
--
-- Run: psql -h localhost -U admin -d learndb -f 02_roles_and_privileges.sql
-- ============================================================

-- ─── 1. Create roles ──────────────────────────────────────────
-- A role = user + group in PostgreSQL (same thing)

-- Drop if exists (for re-runs)
DROP ROLE IF EXISTS app_readonly;
DROP ROLE IF EXISTS app_readwrite;
DROP ROLE IF EXISTS app_admin;
DROP ROLE IF EXISTS alice_dev;
DROP ROLE IF EXISTS bob_dev;

-- Role with login = user account
-- Role without login = group (assigned to users)

CREATE ROLE app_readonly;                        -- group role, no login
CREATE ROLE app_readwrite;                       -- group role, no login
CREATE ROLE app_admin;                           -- group role, no login

CREATE ROLE alice_dev LOGIN PASSWORD 'alice123'; -- actual user
CREATE ROLE bob_dev   LOGIN PASSWORD 'bob123';

-- ─── 2. Grant privileges to group roles ───────────────────────
-- GRANT object-level permissions to the group roles
GRANT CONNECT ON DATABASE learndb TO app_readonly;
GRANT CONNECT ON DATABASE learndb TO app_readwrite;
GRANT CONNECT ON DATABASE learndb TO app_admin;

GRANT USAGE ON SCHEMA public TO app_readonly, app_readwrite, app_admin;

-- readonly: only SELECT
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- readwrite: SELECT + INSERT + UPDATE + DELETE
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_readwrite;

-- admin: all privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_admin;

-- ─── 3. Assign group roles to users ───────────────────────────
GRANT app_readonly  TO bob_dev;    -- bob can only read
GRANT app_readwrite TO alice_dev;  -- alice can read and write

-- ─── 4. Verify what permissions were granted ──────────────────
-- Check which roles a user belongs to
SELECT
    r.rolname                          AS role,
    ARRAY_AGG(m.rolname) FILTER (WHERE m.rolname IS NOT NULL) AS member_of
FROM pg_roles r
LEFT JOIN pg_auth_members am ON r.oid = am.member
LEFT JOIN pg_roles        m  ON am.roleid = m.oid
WHERE r.rolname IN ('alice_dev', 'bob_dev', 'app_readonly', 'app_readwrite')
GROUP BY r.rolname;

-- ─── 5. INHERITANCE pitfall (from AWS session) ────────────────
-- By default INHERIT = true: alice_dev automatically gets app_readwrite privs
-- This can lead to unintended privilege escalation in complex chains

-- BAD: Role chaining (A → B → C → D) — hard to audit
-- If app_readwrite inherits from app_admin, alice gets admin privs unintentionally!

-- FIX: Use NOINHERIT for sensitive roles — must explicitly SET ROLE
CREATE ROLE sensitive_admin NOINHERIT;  -- no auto-inherit

-- To use sensitive_admin's privileges, user must explicitly switch:
-- SET ROLE sensitive_admin;
-- ... do privileged work ...
-- RESET ROLE;

-- ─── 6. Row-Level Security (RLS) ──────────────────────────────
-- Restrict rows based on current user — each user sees only their own data

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own orders
-- current_user = the logged-in PostgreSQL role name
CREATE POLICY orders_isolation ON orders
    USING (user_id = (
        SELECT id FROM users WHERE username = current_user
    ));

-- Superusers bypass RLS by default
-- To make RLS apply to table owner too:
ALTER TABLE orders FORCE ROW LEVEL SECURITY;

-- ─── 7. Least privilege checklist ────────────────────────────
/*
  BEST PRACTICES (from AWS session):

  1. Never share the superuser (postgres) for application connections
     → create a dedicated app role with minimal privs

  2. Avoid:  GRANT ALL ON DATABASE ...
     Prefer: GRANT CONNECT, then specific table grants

  3. Avoid complex role chains (A inherits B inherits C)
     → audit becomes impossible
     → use explicit GRANT per object instead

  4. NOINHERIT for admin roles — require explicit SET ROLE

  5. Rotate passwords regularly — enforce with:
     ALTER ROLE alice_dev VALID UNTIL '2026-12-31';

  6. Revoke CREATE on public schema (default in PG 15+):
     REVOKE CREATE ON SCHEMA public FROM PUBLIC;
     → prevents non-superusers creating objects in public
*/

-- Revoke public create — critical security hardening
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ─── 8. Audit who has what ────────────────────────────────────
-- Table-level permissions
SELECT grantee, table_name, privilege_type
FROM   information_schema.role_table_grants
WHERE  table_schema = 'public'
ORDER  BY grantee, table_name;
