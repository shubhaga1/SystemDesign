-- ============================================================
-- EXTENSIONS & PRIVILEGE ESCALATION
-- Based on AWS session — November 2025 PostgreSQL Anonymizer CVE
--
-- HOW THE ATTACK WORKS:
--   1. Non-superuser has CREATE privilege on public schema
--   2. They create a malicious function with the same name as one
--      used by a superuser extension
--   3. When superuser installs the extension, search_path resolves
--      to public first → superuser executes attacker's function
--   4. Attacker's code now runs with SUPERUSER privileges → full DB access
--
-- Run: psql -h localhost -U admin -d learndb -f 04_extensions_security.sql
-- ============================================================

-- ─── 1. See installed extensions ─────────────────────────────
SELECT name, default_version, installed_version, comment
FROM   pg_available_extensions
ORDER  BY installed_version NULLS LAST, name;

-- ─── 2. Search path — the root cause ─────────────────────────
-- search_path controls which schema is searched first
-- Default search_path = "$user", public
-- If attacker creates a function in public with same name as extension's internal
-- function, it gets called instead when search_path hits public first

SHOW search_path;  -- see current setting

-- VULNERABLE: extension installed with search_path = public first
-- CREATE EXTENSION some_extension;  -- if public schema has malicious function = pwned

-- ─── 3. Simulate the attack vector ───────────────────────────
-- Attacker creates a function in public schema that looks legitimate
-- (in reality this would capture data, create backdoor users, etc.)

-- Step 1: Attacker creates malicious function (they have CREATE on public)
CREATE OR REPLACE FUNCTION public.pg_catalog_version()
RETURNS TEXT AS $$
BEGIN
    -- Real attack: CREATE ROLE hacker SUPERUSER; or COPY secrets to attacker
    RAISE NOTICE '[ATTACK] Malicious function executed with caller privileges!';
    RAISE NOTICE '[ATTACK] Could exfiltrate: SELECT current_user, session_user';
    RETURN 'malicious_result';
END;
$$ LANGUAGE plpgsql;

-- Step 2: Superuser runs something that calls pg_catalog_version()
-- with search_path including public before pg_catalog
SET search_path = public, pg_catalog;
SELECT pg_catalog_version();  -- hits public.pg_catalog_version first = ATTACK!

-- Reset to safe path
RESET search_path;
SELECT pg_catalog_version();  -- now hits real pg_catalog first = safe

-- ─── 4. DEFENSE: Lock down search_path ───────────────────────
-- Set search_path to exclude public for superuser sessions
ALTER ROLE admin SET search_path = pg_catalog, public;

-- For extensions, always specify schema explicitly
-- BAD:   SELECT some_function();                  ← search_path dependent
-- GOOD:  SELECT my_schema.some_function();         ← explicit, safe

-- ─── 5. DEFENSE: Restrict who can create extensions ──────────
-- Extensions can only be created by superusers (default and recommended)
-- Check current extension creation permissions:
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole
FROM   pg_roles
WHERE  rolname NOT LIKE 'pg_%'
ORDER  BY rolsuper DESC;

-- Revoke CREATE from public schema (critical!)
-- This prevents any non-superuser from creating objects in public
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

-- ─── 6. DEFENSE: Extension allow list ────────────────────────
-- In postgresql.conf, restrict which extensions can be installed:
-- shared_preload_libraries = 'pg_stat_statements'

-- Check what extensions are currently loaded:
SELECT extname, extversion, extrelocatable
FROM   pg_extension;

-- ─── 7. DEFENSE: Monitor extension creation ──────────────────
-- Log whenever extensions are created/dropped (via audit trigger)

CREATE TABLE IF NOT EXISTS extension_audit_log (
    id          SERIAL PRIMARY KEY,
    action      VARCHAR(20),
    extname     VARCHAR(100),
    executed_by VARCHAR(100),
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to log extension events
-- (In production: use pgaudit extension for comprehensive audit logging)
CREATE OR REPLACE FUNCTION log_extension_event()
RETURNS event_trigger AS $$
DECLARE
    obj record;
BEGIN
    FOR obj IN SELECT * FROM pg_event_trigger_ddl_commands() LOOP
        IF obj.command_tag IN ('CREATE EXTENSION', 'DROP EXTENSION') THEN
            INSERT INTO extension_audit_log (action, extname, executed_by)
            VALUES (obj.command_tag, obj.object_identity, current_user);
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to DDL events
DROP EVENT TRIGGER IF EXISTS audit_extensions;
CREATE EVENT TRIGGER audit_extensions
    ON ddl_command_end
    WHEN TAG IN ('CREATE EXTENSION', 'DROP EXTENSION')
    EXECUTE FUNCTION log_extension_event();

-- ─── 8. pgaudit — production audit extension ─────────────────
-- pgaudit logs all DDL, DML, role changes to PostgreSQL log
-- Enable in postgresql.conf:
--   shared_preload_libraries = 'pgaudit'
--   pgaudit.log = 'ddl, role, read, write'

-- Check if pgaudit is available:
SELECT name, default_version FROM pg_available_extensions WHERE name = 'pgaudit';

-- ─── Summary ─────────────────────────────────────────────────
/*
  EXTENSION ATTACK DEFENSES:
  1. REVOKE CREATE ON SCHEMA public FROM PUBLIC
     → non-superusers can't plant malicious functions

  2. Set explicit search_path per role:
     ALTER ROLE app_user SET search_path = myschema, pg_catalog;
     → public never searched first

  3. Only superusers create extensions (default — don't change)

  4. Maintain an extension allow list
     → remove unused extensions (each is a potential attack surface)

  5. Audit extension creation with event triggers or pgaudit

  6. Always prefix schema in extension code: pg_catalog.function()
     → immune to search_path manipulation
*/
