-- ─────────────────────────────────────────────────────────────────────────────
-- SQL FUNDAMENTALS — Day 1
-- DDL, DML, DQL, Data Types, SELECT, INSERT, DELETE, ORDER BY
--
-- SQL categories:
--   DDL = Data Definition Language  → CREATE, ALTER, DROP  (structure)
--   DML = Data Manipulation Language → INSERT, UPDATE, DELETE (data)
--   DQL = Data Query Language        → SELECT (read data)
--
-- Data types:
--   INTEGER       → whole numbers: 1, 2, -1
--   DATE / TEXT   → dates: '2022-10-01'
--   VARCHAR(n)    → text up to n chars: 'Baby Milk'
--   DECIMAL(p,s)  → decimal: 1234.45 (p=total digits, s=after decimal)
-- ─────────────────────────────────────────────────────────────────────────────

-- ── DDL: CREATE TABLE ─────────────────────────────────────────────────────────
DROP TABLE IF EXISTS amazon_orders;

CREATE TABLE amazon_orders (
    order_id       INTEGER,
    order_date     TEXT,           -- stored as 'YYYY-MM-DD'
    product_name   VARCHAR(100),
    total_price    DECIMAL(6,2),
    payment_method VARCHAR(20)
);

-- ── DML: INSERT rows ──────────────────────────────────────────────────────────
INSERT INTO amazon_orders VALUES (1, '2022-10-01', 'Baby Milk',   30.5,  'UPI');
INSERT INTO amazon_orders VALUES (2, '2022-10-02', 'Baby Powder', 130,   'Credit Card');
INSERT INTO amazon_orders VALUES (3, '2022-10-01', 'Baby Cream',  30.5,  'UPI');
INSERT INTO amazon_orders VALUES (4, '2022-10-02', 'Baby Soap',   130,   'Credit Card');

-- ── DQL: SELECT — read data ───────────────────────────────────────────────────
SELECT '=== All rows ===' AS section;
SELECT * FROM amazon_orders;

SELECT '=== Specific columns ===' AS section;
SELECT product_name, order_date, total_price FROM amazon_orders;

-- LIMIT — SQLite uses LIMIT (SQL Server uses TOP)
SELECT '=== First row only (LIMIT 1) ===' AS section;
SELECT * FROM amazon_orders LIMIT 1;
-- SQL Server equivalent: SELECT TOP 1 * FROM amazon_orders

-- ── ORDER BY — sort results ───────────────────────────────────────────────────
SELECT '=== ORDER BY date desc, product desc ===' AS section;
SELECT * FROM amazon_orders
ORDER BY order_date DESC, product_name DESC, payment_method;
-- Multiple columns: sort by first, ties broken by second, etc.
-- DESC = descending (Z→A, newest first)
-- ASC  = ascending  (A→Z, oldest first) — default

-- ── DML: DELETE ───────────────────────────────────────────────────────────────
SELECT '=== Before delete ===' AS section;
SELECT COUNT(*) AS row_count FROM amazon_orders;

-- Delete with filter — only removes matching rows
DELETE FROM amazon_orders WHERE payment_method = 'Credit Card';

SELECT '=== After delete (Credit Card rows removed) ===' AS section;
SELECT * FROM amazon_orders;

-- Delete ALL rows (no WHERE) — table stays, data gone
-- DELETE FROM amazon_orders;

-- Drop table entirely (structure + data gone)
-- DROP TABLE amazon_orders;

-- ── Data type cheat sheet ─────────────────────────────────────────────────────
SELECT '=== Data types ===' AS section;
SELECT '
Type             | Example           | Notes
─────────────────────────────────────────────────────────────────
INTEGER          | 1, -5, 1000       | whole numbers
DECIMAL(6,2)     | 1234.56           | 6 total digits, 2 after decimal
VARCHAR(100)     | Baby Milk         | variable text up to 100 chars
TEXT             | any length text   | SQLite preferred over VARCHAR
DATE / TEXT      | 2022-10-01        | store as YYYY-MM-DD for sorting
BOOLEAN          | 0 or 1            | SQLite has no bool, uses 0/1
' AS data_types;
