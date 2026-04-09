-- ─────────────────────────────────────────────────────────────────────────────
-- SQL BASICS — WHERE, GROUP BY, HAVING, ORDER BY
--
-- Key rule:
--   WHERE   filters ROWS   (before grouping)   → works on individual row values
--   HAVING  filters GROUPS (after grouping)    → works on aggregate results
--
-- Execution order (not the order you write it):
--   FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Setup: create and populate employees table ────────────────────────────────
CREATE TABLE emp (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    department TEXT    NOT NULL,
    salary     REAL    NOT NULL,
    manager_id INTEGER           -- NULL means top-level manager
);

INSERT INTO emp VALUES
    (1,  'Alice',   'Engineering', 95000, NULL),
    (2,  'Bob',     'Engineering', 87000, 1),
    (3,  'Charlie', 'Engineering', 82000, 1),
    (4,  'Diana',   'Marketing',   72000, NULL),
    (5,  'Eve',     'Marketing',   68000, 4),
    (6,  'Frank',   'Marketing',   61000, 4),
    (7,  'Grace',   'HR',          55000, NULL),
    (8,  'Henry',   'HR',          52000, 7),
    (9,  'Ivy',     'Engineering', 91000, 1),
    (10, 'Jack',    'Marketing',   74000, 4);

-- ── 1. WHERE — filter individual rows ─────────────────────────────────────────
-- Employees with salary > 10000 (all of them in this case)
-- More useful: salary > 80000
SELECT '=== WHERE sal > 80000 ===' AS query;
SELECT name, department, salary
FROM   emp
WHERE  salary > 80000
ORDER  BY salary DESC;

-- ── 2. GROUP BY + aggregate functions ─────────────────────────────────────────
SELECT '=== GROUP BY department ===' AS query;
SELECT
    department,
    COUNT(*)        AS headcount,
    AVG(salary)     AS avg_salary,
    MAX(salary)     AS max_salary,
    MIN(salary)     AS min_salary,
    SUM(salary)     AS total_cost
FROM   emp
GROUP  BY department
ORDER  BY avg_salary DESC;

-- ── 3. HAVING — filter groups AFTER aggregation ───────────────────────────────
-- Departments where average salary > 10000 (all depts qualify here)
-- Real use: avg_salary > 70000 (only Engineering and Marketing)
SELECT '=== HAVING avg(sal) > 70000 ===' AS query;
SELECT
    department,
    ROUND(AVG(salary), 2) AS avg_salary,
    COUNT(*)               AS headcount
FROM   emp
GROUP  BY department
HAVING AVG(salary) > 70000
ORDER  BY avg_salary DESC;

-- ── 4. WHERE + GROUP BY + HAVING together ─────────────────────────────────────
-- Among employees with salary > 60000,
-- show departments where the average of those salaries > 80000
SELECT '=== WHERE + GROUP BY + HAVING ===' AS query;
SELECT
    department,
    ROUND(AVG(salary), 2) AS avg_high_earner_salary,
    COUNT(*)               AS count_above_60k
FROM   emp
WHERE  salary > 60000          -- filter rows FIRST (removes Henry 52k, Grace 55k, Frank 61k = keep > 60k)
GROUP  BY department           -- then group
HAVING AVG(salary) > 80000    -- then filter groups
ORDER  BY avg_high_earner_salary DESC;

-- ── 5. WHERE vs HAVING — the key difference ───────────────────────────────────
SELECT '=== WHERE vs HAVING difference ===' AS query;

-- This works — salary is a column value (row level)
SELECT name, salary FROM emp WHERE salary > 80000;

-- This would FAIL — AVG() cannot be in WHERE:
-- SELECT name FROM emp WHERE AVG(salary) > 80000;  ← ERROR

-- This works — AVG() in HAVING (group level)
SELECT department, AVG(salary)
FROM   emp
GROUP  BY department
HAVING AVG(salary) > 80000;

-- ── 6. ORDER BY + LIMIT ───────────────────────────────────────────────────────
SELECT '=== Top 3 earners ===' AS query;
SELECT name, department, salary
FROM   emp
ORDER  BY salary DESC
LIMIT  3;

SELECT '=== Bottom 3 earners ===' AS query;
SELECT name, department, salary
FROM   emp
ORDER  BY salary ASC
LIMIT  3;
