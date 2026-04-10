-- ─────────────────────────────────────────────────────────────────────────────
-- DDL vs DML — Definitions, Constraints, ALTER, INSERT, UPDATE, DELETE
--
-- DDL = Data Definition Language  → changes structure (CREATE, ALTER, DROP)
-- DML = Data Manipulation Language → changes data    (INSERT, UPDATE, DELETE)
--
-- NOTE: ALTER TABLE syntax differs between databases:
--   SQL Server:  ALTER TABLE t ALTER COLUMN col datetime
--   PostgreSQL:  ALTER TABLE t ALTER COLUMN col TYPE date
--   SQLite:      does NOT support ALTER COLUMN — must recreate table
-- ─────────────────────────────────────────────────────────────────────────────

-- ── 1. CREATE TABLE ───────────────────────────────────────────────────────────
DROP TABLE IF EXISTS amazon_orders;

CREATE TABLE amazon_orders (
    order_id       INTEGER,
    order_date     TEXT,           -- SQLite has no native DATE type, stored as TEXT
    product_name   TEXT,
    total_price    DECIMAL(6,2),
    payment_method TEXT
);

SELECT '=== 1. Basic table created ===' AS section;
SELECT * FROM amazon_orders;       -- empty

-- ── 2. INSERT — adding rows ───────────────────────────────────────────────────
SELECT '=== 2. INSERT rows ===' AS section;

INSERT INTO amazon_orders VALUES (5, '2022-10-01 12:05:12', 'Shoes',  132.5, 'UPI');
INSERT INTO amazon_orders VALUES (6, '2022-10-01 12:05:12', NULL,     132.5, 'UPI');  -- NULL = no value
INSERT INTO amazon_orders VALUES (7, '2022-10-01 12:05:12', 'null',   132.5, 'UPI');  -- 'null' = string "null", NOT null

SELECT * FROM amazon_orders;

-- ── 3. ALTER TABLE — add/drop columns (DDL) ───────────────────────────────────
SELECT '=== 3. ALTER TABLE — add and drop column ===' AS section;

-- Add a column to existing table
ALTER TABLE amazon_orders ADD COLUMN username TEXT;
ALTER TABLE amazon_orders ADD COLUMN category TEXT;

-- Drop a column
ALTER TABLE amazon_orders DROP COLUMN category;

SELECT * FROM amazon_orders;    -- username column exists, category gone

-- ── 4. CONSTRAINTS — rules enforced by the database ──────────────────────────
SELECT '=== 4. CONSTRAINTS ===' AS section;
-- Constraints are rules the DB enforces automatically.
-- Violation = insert/update rejected with an error.

DROP TABLE IF EXISTS a_orders;

CREATE TABLE a_orders (
    order_id       INTEGER,
    order_date     TEXT,
    product_name   TEXT,
    total_price    DECIMAL(6,2),

    -- CHECK constraint: only allow specific values
    payment_method TEXT CHECK (payment_method IN ('UPI', 'CREDIT CARD'))
                        DEFAULT 'UPI',       -- DEFAULT: value used when not specified

    -- CHECK constraint: value must satisfy condition
    discount       INTEGER CHECK (discount <= 20),

    -- DEFAULT constraint: fallback value
    category       TEXT DEFAULT 'Mens Wear',

    -- PRIMARY KEY = UNIQUE + NOT NULL (composite key here)
    -- combination of order_id + product_name must be unique
    PRIMARY KEY (order_id, product_name)
);

-- Valid insert — all constraints satisfied
INSERT INTO a_orders VALUES (1, '2022-10-01', 'Shirts', 132.5, 'UPI', 20, 'Kids Wear');

-- Insert with defaults — payment_method uses DEFAULT 'UPI', category uses DEFAULT 'Mens Wear'
INSERT INTO a_orders (order_id, order_date, product_name, total_price)
VALUES (2, '2022-10-01', 'Jeans', 132.5);

SELECT * FROM a_orders;

-- ── 5. DELETE — remove rows (DML) ────────────────────────────────────────────
SELECT '=== 5. DELETE with WHERE ===' AS section;

-- Always use WHERE — without it, ALL rows are deleted
DELETE FROM a_orders WHERE product_name = 'Jeans';

SELECT * FROM a_orders;

-- ── 6. UPDATE — modify existing rows (DML) ────────────────────────────────────
SELECT '=== 6. UPDATE ===' AS section;

-- Update all rows (no WHERE — dangerous in production)
UPDATE a_orders SET discount = 10;

-- Update specific rows
UPDATE a_orders SET discount = 15 WHERE order_id = 1;

-- Update multiple columns at once
UPDATE a_orders
SET    product_name = 'Jeans2', payment_method = 'CREDIT CARD'
WHERE  product_name = 'Jeans';

SELECT * FROM a_orders;

-- ── 7. Key differences — NULL vs 'null' ──────────────────────────────────────
SELECT '=== 7. NULL vs string null ===' AS section;

DROP TABLE IF EXISTS null_demo;
CREATE TABLE null_demo (id INTEGER, name TEXT);
INSERT INTO null_demo VALUES (1, NULL);     -- actual NULL — no value
INSERT INTO null_demo VALUES (2, 'null');   -- string "null" — a value!
INSERT INTO null_demo VALUES (3, '');       -- empty string — a value!

SELECT id, name,
    CASE WHEN name IS NULL     THEN 'is NULL'
         WHEN name = 'null'    THEN 'string null'
         WHEN name = ''        THEN 'empty string'
         ELSE 'has value'
    END AS type
FROM null_demo;

-- NULL check: always use IS NULL / IS NOT NULL (never = NULL)
SELECT * FROM null_demo WHERE name IS NULL;     -- ✅ correct
-- SELECT * FROM null_demo WHERE name = NULL;   -- ❌ always returns nothing

-- ── 8. Constraint summary ─────────────────────────────────────────────────────
SELECT '=== 8. Constraint types ===' AS section;
SELECT '
Constraint       | What it enforces
─────────────────────────────────────────────────────────
PRIMARY KEY      | UNIQUE + NOT NULL — row identifier
NOT NULL         | column must have a value
UNIQUE           | no two rows can have same value
CHECK            | value must satisfy condition (discount <= 20)
DEFAULT          | value used when not specified in INSERT
FOREIGN KEY      | value must exist in another table (referential integrity)
' AS constraints;
