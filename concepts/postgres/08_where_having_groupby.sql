-- ─────────────────────────────────────────────────────────────────────────────
-- WHERE vs HAVING vs GROUP BY
--
-- Key rule:
--   WHERE   filters ROWS   (before grouping)  → works on column values
--   HAVING  filters GROUPS (after grouping)   → works on aggregate results
--
-- Execution order (NOT the order you write):
--   FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT
-- ─────────────────────────────────────────────────────────────────────────────

DROP TABLE IF EXISTS emp;

CREATE TABLE emp (
    id         INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    department TEXT    NOT NULL,
    salary     NUMERIC NOT NULL,
    manager_id INTEGER
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

-- ── 1. WHERE — filter individual rows (row level) ─────────────────────────────
-- Question: show employees with salary > 10000
SELECT '=== 1. WHERE salary > 10000 ===' AS section;
SELECT name, department, salary
FROM   emp
WHERE  salary > 10000       -- every row checked individually
ORDER  BY salary DESC;

-- ── 2. GROUP BY — aggregate rows into groups ──────────────────────────────────
SELECT '=== 2. GROUP BY department ===' AS section;
SELECT
    department,
    COUNT(*)              AS headcount,
    AVG(salary)           AS avg_salary,
    MAX(salary)           AS max_salary,
    MIN(salary)           AS min_salary,
    SUM(salary)           AS total_cost
FROM   emp
GROUP  BY department
ORDER  BY avg_salary DESC;

-- ── 3. HAVING — filter after grouping (group level) ───────────────────────────
-- Question: departments where avg salary > 10000
SELECT '=== 3. HAVING avg(salary) > 10000 ===' AS section;
SELECT
    department,
    ROUND(AVG(salary), 2) AS avg_salary,
    COUNT(*)               AS headcount
FROM   emp
GROUP  BY department
HAVING AVG(salary) > 10000   -- applied AFTER groups are formed
ORDER  BY avg_salary DESC;

-- More realistic: departments with avg salary > 70000
SELECT '=== 3b. HAVING avg(salary) > 70000 ===' AS section;
SELECT
    department,
    ROUND(AVG(salary), 2) AS avg_salary,
    COUNT(*)               AS headcount
FROM   emp
GROUP  BY department
HAVING AVG(salary) > 70000
ORDER  BY avg_salary DESC;

-- ── 4. WHERE + GROUP BY + HAVING together ─────────────────────────────────────
-- Among employees earning > 60000,
-- show departments where avg of those salaries > 80000
SELECT '=== 4. WHERE + GROUP BY + HAVING combined ===' AS section;
SELECT
    department,
    ROUND(AVG(salary), 2) AS avg_salary,
    COUNT(*)               AS count_above_60k
FROM   emp
WHERE  salary > 60000          -- step 1: filter rows (removes Grace 55k, Henry 52k)
GROUP  BY department           -- step 2: group remaining rows
HAVING AVG(salary) > 80000    -- step 3: filter groups by aggregate
ORDER  BY avg_salary DESC;

-- ── 5. WHERE vs HAVING — why you can't swap them ──────────────────────────────
SELECT '=== 5. WHERE vs HAVING — key difference ===' AS section;

-- WHERE works on column values (row level) ✅
SELECT name, salary FROM emp WHERE salary > 80000;

-- HAVING works on aggregates (group level) ✅
SELECT department, AVG(salary)
FROM   emp
GROUP  BY department
HAVING AVG(salary) > 80000;

-- ── 6. Top/Bottom earners ─────────────────────────────────────────────────────
SELECT '=== 6. Top 3 earners ===' AS section;
SELECT name, department, salary
FROM   emp
ORDER  BY salary DESC
LIMIT  3;

SELECT '=== 6b. Bottom 3 earners ===' AS section;
SELECT name, department, salary
FROM   emp
ORDER  BY salary ASC
LIMIT  3;
