-- ============================================================
-- POSTGRES BASICS — DDL, DML, indexes, joins
-- Run: psql -h localhost -U admin -d learndb -f 01_basics.sql
-- ============================================================

-- ─── Setup ───────────────────────────────────────────────────
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS users;

-- ─── CREATE TABLE ────────────────────────────────────────────
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,           -- auto-increment integer PK
    username   VARCHAR(50)  NOT NULL UNIQUE, -- unique, non-null
    email      VARCHAR(100) NOT NULL UNIQUE,
    role       VARCHAR(20)  NOT NULL DEFAULT 'viewer',  -- default value
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),     -- timezone-aware timestamp
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE orders (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product    VARCHAR(100) NOT NULL,
    amount     NUMERIC(10,2) NOT NULL CHECK (amount > 0),   -- CHECK constraint
    status     VARCHAR(20)  NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','shipped','delivered','cancelled')),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ─── INSERT ───────────────────────────────────────────────────
INSERT INTO users (username, email, role) VALUES
    ('shubham',  'shubham@example.com',  'admin'),
    ('alice',    'alice@example.com',    'editor'),
    ('bob',      'bob@example.com',      'viewer'),
    ('charlie',  'charlie@example.com',  'editor'),
    ('diana',    'diana@example.com',    'viewer');

INSERT INTO orders (user_id, product, amount, status) VALUES
    (1, 'MacBook Pro',   2499.00, 'delivered'),
    (1, 'AirPods',        199.00, 'shipped'),
    (2, 'iPhone 15',     1199.00, 'delivered'),
    (3, 'iPad Mini',      599.00, 'pending'),
    (3, 'Apple Watch',    399.00, 'cancelled'),
    (4, 'Magic Keyboard', 129.00, 'delivered');

-- ─── SELECT basics ───────────────────────────────────────────
SELECT * FROM users;

-- WHERE, ORDER BY, LIMIT
SELECT username, email, role
FROM   users
WHERE  role != 'viewer'
ORDER  BY username
LIMIT  3;

-- ─── JOINS ───────────────────────────────────────────────────
-- INNER JOIN — only rows with match in both tables
SELECT u.username, o.product, o.amount, o.status
FROM   users  u
JOIN   orders o ON u.id = o.user_id
ORDER  BY u.username, o.amount DESC;

-- LEFT JOIN — all users, even those with no orders
SELECT u.username, COUNT(o.id) AS order_count, COALESCE(SUM(o.amount), 0) AS total_spent
FROM   users  u
LEFT   JOIN orders o ON u.id = o.user_id
GROUP  BY u.id, u.username
ORDER  BY total_spent DESC;

-- ─── AGGREGATE functions ──────────────────────────────────────
SELECT
    status,
    COUNT(*)        AS count,
    AVG(amount)     AS avg_amount,
    MIN(amount)     AS min_amount,
    MAX(amount)     AS max_amount,
    SUM(amount)     AS total
FROM  orders
GROUP BY status
HAVING COUNT(*) > 0    -- HAVING filters after GROUP BY (WHERE filters before)
ORDER BY total DESC;

-- ─── WINDOW functions ─────────────────────────────────────────
-- Rank orders by amount per user
SELECT
    u.username,
    o.product,
    o.amount,
    RANK()       OVER (PARTITION BY u.id ORDER BY o.amount DESC) AS rank_by_amount,
    SUM(o.amount) OVER (PARTITION BY u.id)                       AS user_total,
    SUM(o.amount) OVER ()                                         AS grand_total
FROM  users  u
JOIN  orders o ON u.id = o.user_id
ORDER BY u.username, rank_by_amount;

-- ─── INDEXES ──────────────────────────────────────────────────
-- B-Tree index (default) — good for =, <, >, BETWEEN, ORDER BY
CREATE INDEX idx_orders_user_id  ON orders(user_id);
CREATE INDEX idx_orders_status   ON orders(status);
CREATE INDEX idx_users_email     ON users(email);

-- Composite index — useful when queries filter by both columns together
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- See query plan — does it use index?
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = 1 AND status = 'delivered';

-- ─── UPDATE and DELETE ────────────────────────────────────────
UPDATE users SET role = 'editor' WHERE username = 'bob';

DELETE FROM orders WHERE status = 'cancelled';

-- ─── CTE (Common Table Expression) ───────────────────────────
-- Named subquery — read top from bottom
WITH high_spenders AS (
    SELECT user_id, SUM(amount) AS total
    FROM   orders
    GROUP  BY user_id
    HAVING SUM(amount) > 500
)
SELECT u.username, hs.total
FROM   users       u
JOIN   high_spenders hs ON u.id = hs.user_id
ORDER  BY hs.total DESC;
