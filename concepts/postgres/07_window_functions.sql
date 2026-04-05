-- ============================================================
-- WINDOW FUNCTIONS & IMPORTANT SQL FUNCTIONS
-- RANK, DENSE_RANK, ROW_NUMBER, LAG, LEAD, COALESCE, NULLIF,
-- CASE, GREATEST, LEAST, STRING_AGG, ARRAY_AGG, FILTER
--
-- Run: psql -h localhost -U admin -d learndb -f 07_window_functions.sql
-- ============================================================

-- ─── Setup ───────────────────────────────────────────────────
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(50),
    dept       VARCHAR(50),
    salary     NUMERIC(10,2),
    manager_id INTEGER REFERENCES employees(id),
    hire_date  DATE
);

INSERT INTO employees (name, dept, salary, manager_id, hire_date) VALUES
    ('Shubham', 'Engineering', 95000, NULL,   '2021-01-15'),
    ('Alice',   'Engineering', 87000, 1,      '2022-03-01'),
    ('Bob',     'Engineering', 87000, 1,      '2022-05-10'),
    ('Carol',   'Marketing',   72000, NULL,   '2020-06-20'),
    ('Diana',   'Marketing',   68000, 4,      '2023-01-05'),
    ('Eve',     'Marketing',   72000, 4,      '2021-09-15'),
    ('Frank',   'HR',          65000, NULL,   '2019-11-01'),
    ('Grace',   'HR',          60000, 7,      '2023-07-20');

CREATE TABLE sales (
    id        SERIAL PRIMARY KEY,
    emp_id    INTEGER REFERENCES employees(id),
    month     DATE,
    revenue   NUMERIC(12,2)
);

INSERT INTO sales (emp_id, month, revenue) VALUES
    (2, '2026-01-01', 45000), (2, '2026-02-01', 52000), (2, '2026-03-01', 48000),
    (3, '2026-01-01', 38000), (3, '2026-02-01', 41000), (3, '2026-03-01', 55000),
    (5, '2026-01-01', 62000), (5, '2026-02-01', 58000), (5, '2026-03-01', 70000),
    (6, '2026-01-01', 33000), (6, '2026-02-01', 29000), (6, '2026-03-01', 44000);

-- ─── 1. RANK, DENSE_RANK, ROW_NUMBER ────────────────────────
-- All three number rows, but handle TIES differently
SELECT
    name,
    dept,
    salary,
    RANK()       OVER (PARTITION BY dept ORDER BY salary DESC) AS rank,
    DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS dense_rank,
    ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC) AS row_num
FROM employees
ORDER BY dept, salary DESC;

/*
  RANK:        1,1,3      (tie = same rank, next rank skips)
  DENSE_RANK:  1,1,2      (tie = same rank, next rank does NOT skip)
  ROW_NUMBER:  1,2,3      (always unique — arbitrary tiebreak)

  Use RANK       → "top 3 employees" (gap after tie is acceptable)
  Use DENSE_RANK → "2nd highest salary" (no gaps wanted)
  Use ROW_NUMBER → pagination, deduplication (unique row identifier)
*/

-- Find the highest-paid employee per department
SELECT name, dept, salary FROM (
    SELECT
        name, dept, salary,
        RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rnk
    FROM employees
) ranked
WHERE rnk = 1;

-- ─── 2. LAG and LEAD — compare with previous/next row ────────
-- LAG:  look at the PREVIOUS row's value
-- LEAD: look at the NEXT row's value

SELECT
    e.name,
    s.month,
    s.revenue,
    LAG(s.revenue)  OVER (PARTITION BY s.emp_id ORDER BY s.month) AS prev_month_rev,
    LEAD(s.revenue) OVER (PARTITION BY s.emp_id ORDER BY s.month) AS next_month_rev,
    s.revenue - LAG(s.revenue) OVER (PARTITION BY s.emp_id ORDER BY s.month)
                                                                   AS month_over_month_change
FROM sales s
JOIN employees e ON e.id = s.emp_id
ORDER BY e.name, s.month;

-- ─── 3. Running totals and moving averages ────────────────────
SELECT
    e.name,
    s.month,
    s.revenue,
    SUM(s.revenue) OVER (PARTITION BY s.emp_id ORDER BY s.month
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                         AS running_total,
    ROUND(AVG(s.revenue) OVER (PARTITION BY s.emp_id ORDER BY s.month
                                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0)
                         AS moving_avg_3m   -- 3-month rolling average
FROM sales s
JOIN employees e ON e.id = s.emp_id
ORDER BY e.name, s.month;

-- ─── 4. COALESCE — return first non-null value ────────────────
-- Use when a column might be NULL and you want a default

SELECT
    name,
    manager_id,
    COALESCE(manager_id::TEXT, 'No Manager')   AS manager_label,
    COALESCE(NULL, NULL, 'third',  'fourth')   AS first_non_null
FROM employees;

/*
  COALESCE(a, b, c)  →  returns first non-NULL
  Common use:
    COALESCE(discount, 0)           → treat NULL discount as 0
    COALESCE(nickname, first_name)  → fallback to first_name if no nickname
    COALESCE(SUM(amount), 0)        → prevent NULL in aggregation
*/

-- ─── 5. NULLIF — return NULL if two values are equal ─────────
-- Useful for "divide by zero" protection
SELECT
    dept,
    SUM(salary)  AS total_salary,
    COUNT(*)     AS headcount,
    -- Without NULLIF: division by zero error if headcount = 0
    ROUND(SUM(salary) / NULLIF(COUNT(*), 0), 2)  AS avg_salary
FROM employees
GROUP BY dept;

/*
  NULLIF(a, b)  →  returns NULL if a = b, otherwise returns a
  Classic use:  avoid division by zero
    revenue / NULLIF(quantity, 0)   →  NULL instead of error
*/

-- ─── 6. CASE — conditional logic in SQL ───────────────────────
SELECT
    name,
    salary,
    CASE
        WHEN salary >= 90000 THEN 'Senior'
        WHEN salary >= 75000 THEN 'Mid'
        WHEN salary >= 65000 THEN 'Junior'
        ELSE 'Entry'
    END                             AS level,

    -- Simple CASE (equality check only)
    CASE dept
        WHEN 'Engineering' THEN 'Tech'
        WHEN 'Marketing'   THEN 'Business'
        ELSE 'Support'
    END                             AS division
FROM employees
ORDER BY salary DESC;

-- CASE in aggregate (conditional counting)
SELECT
    dept,
    COUNT(*)                                            AS total,
    COUNT(CASE WHEN salary >= 80000 THEN 1 END)         AS senior_count,
    COUNT(CASE WHEN manager_id IS NULL THEN 1 END)      AS managers,
    ROUND(AVG(CASE WHEN salary >= 80000 THEN salary END), 0) AS avg_senior_salary
FROM employees
GROUP BY dept;

-- ─── 7. STRING_AGG — concatenate strings by group ────────────
SELECT
    dept,
    STRING_AGG(name, ', ' ORDER BY name)  AS team_members,
    COUNT(*)                               AS headcount
FROM employees
GROUP BY dept
ORDER BY dept;

-- ─── 8. ARRAY_AGG — collect values into an array ─────────────
SELECT
    dept,
    ARRAY_AGG(name     ORDER BY salary DESC)  AS names_by_salary,
    ARRAY_AGG(salary   ORDER BY salary DESC)  AS salaries,
    ARRAY_AGG(DISTINCT dept)                  AS dept_dedup  -- DISTINCT inside
FROM employees
GROUP BY dept;

-- ─── 9. FILTER — conditional aggregate ───────────────────────
-- Cleaner than CASE inside COUNT/SUM
SELECT
    dept,
    COUNT(*)                                           AS total,
    COUNT(*) FILTER (WHERE salary >= 80000)            AS high_earners,
    COUNT(*) FILTER (WHERE manager_id IS NULL)         AS managers,
    ROUND(AVG(salary) FILTER (WHERE salary < 80000), 0) AS avg_non_senior
FROM employees
GROUP BY dept
ORDER BY dept;

/*
  FILTER (WHERE condition)  →  aggregate only rows matching condition
  Equivalent to:  SUM(CASE WHEN cond THEN val ELSE 0 END)
  But cleaner and readable.
*/

-- ─── 10. GREATEST / LEAST ────────────────────────────────────
SELECT
    GREATEST(10, 20, 5, 30, 15)     AS greatest_value,  -- 30
    LEAST(10, 20, 5, 30, 15)        AS least_value,      -- 5
    GREATEST(salary, 70000)         AS floor_salary,     -- apply minimum salary
    LEAST(salary, 90000)            AS capped_salary     -- cap at max
FROM employees;

-- ─── 11. NTILE — divide rows into N buckets ──────────────────
SELECT
    name,
    dept,
    salary,
    NTILE(4) OVER (ORDER BY salary DESC)  AS salary_quartile
    -- 1 = top 25%, 2 = next 25%, etc.
FROM employees
ORDER BY salary DESC;

-- ─── 12. PERCENT_RANK, CUME_DIST ─────────────────────────────
SELECT
    name,
    salary,
    ROUND(PERCENT_RANK() OVER (ORDER BY salary) * 100, 1) AS percentile,
    ROUND(CUME_DIST()    OVER (ORDER BY salary) * 100, 1) AS cumulative_pct
FROM employees
ORDER BY salary;

/*
  PERCENT_RANK:  what % of rows have a strictly lower value
  CUME_DIST:     what % of rows have a value <= current
*/
