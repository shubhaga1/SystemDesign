-- ─────────────────────────────────────────────────────────────────────────────
-- PIVOT — rows to columns using CASE WHEN
--
-- Problem: data stored as rows (one row per salary component type)
-- Goal:    show each component as a separate column per employee
--
-- Technique: conditional aggregation
--   SUM(CASE WHEN type = 'salary' THEN val END) AS salary
--
-- This is called a PIVOT — rotating row values into column headers.
-- SQL has no built-in PIVOT in SQLite/Postgres, so we use CASE WHEN.
-- ─────────────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS emp_compensation;

CREATE TABLE emp_compensation (
    emp_id                INTEGER,
    salary_component_type TEXT,
    val                   NUMERIC
);

INSERT INTO emp_compensation VALUES
    (1, 'salary',       10000),
    (1, 'bonus',        5000),
    (1, 'hike_percent', 10),
    (2, 'salary',       15000),
    (2, 'bonus',        7000),
    (2, 'hike_percent', 8),
    (3, 'salary',       12000),
    (3, 'bonus',        6000),
    (3, 'hike_percent', 7);

-- ── See raw data first ────────────────────────────────────────────────────────
SELECT '=== Raw data (rows) ===' AS section;
SELECT * FROM emp_compensation;
-- emp_id | salary_component_type | val
-- 1      | salary                | 10000
-- 1      | bonus                 | 5000
-- 1      | hike_percent          | 10
-- ...

-- ── PIVOT: rows → columns ─────────────────────────────────────────────────────
SELECT '=== Pivoted (columns) ===' AS section;
SELECT
    emp_id,
    SUM(CASE WHEN salary_component_type = 'salary'       THEN val END) AS salary,
    SUM(CASE WHEN salary_component_type = 'bonus'        THEN val END) AS bonus,
    SUM(CASE WHEN salary_component_type = 'hike_percent' THEN val END) AS hike_percent
FROM   emp_compensation
GROUP  BY emp_id;
-- emp_id | salary | bonus | hike_percent
-- 1      | 10000  | 5000  | 10
-- 2      | 15000  | 7000  | 8
-- 3      | 12000  | 6000  | 7

-- ── How CASE WHEN works here ──────────────────────────────────────────────────
-- For emp_id = 1, three rows exist:
--   row 1: type='salary',       val=10000  → CASE matches 'salary'  → SUM gets 10000
--   row 2: type='bonus',        val=5000   → CASE matches 'bonus'   → SUM gets 5000
--   row 3: type='hike_percent', val=10     → CASE matches 'hike_percent' → SUM gets 10
--
-- After GROUP BY emp_id, SUM collapses all three rows into one:
--   salary=10000, bonus=5000, hike_percent=10

-- ── With COALESCE to replace NULL with 0 ─────────────────────────────────────
-- If an employee has no bonus entry, CASE returns NULL → SUM = NULL
-- COALESCE(SUM(...), 0) returns 0 instead
SELECT '=== With COALESCE (NULL → 0) ===' AS section;
SELECT
    emp_id,
    COALESCE(SUM(CASE WHEN salary_component_type = 'salary'       THEN val END), 0) AS salary,
    COALESCE(SUM(CASE WHEN salary_component_type = 'bonus'        THEN val END), 0) AS bonus,
    COALESCE(SUM(CASE WHEN salary_component_type = 'hike_percent' THEN val END), 0) AS hike_percent
FROM   emp_compensation
GROUP  BY emp_id
ORDER  BY emp_id;

-- ── UNPIVOT — reverse: columns back to rows ───────────────────────────────────
-- Use UNION ALL to go from columns → rows
SELECT '=== Unpivot (columns → rows) ===' AS section;
SELECT emp_id, 'salary'       AS component, salary       AS val FROM (
    SELECT emp_id,
           SUM(CASE WHEN salary_component_type = 'salary' THEN val END) AS salary
    FROM emp_compensation GROUP BY emp_id
)
UNION ALL
SELECT emp_id, 'bonus'        AS component, bonus        AS val FROM (
    SELECT emp_id,
           SUM(CASE WHEN salary_component_type = 'bonus' THEN val END) AS bonus
    FROM emp_compensation GROUP BY emp_id
)
ORDER BY emp_id, component;
