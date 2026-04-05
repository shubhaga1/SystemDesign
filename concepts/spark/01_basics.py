"""
APACHE SPARK BASICS

WHAT IS SPARK?
  Distributed data processing engine — runs computations across many machines.
  Think of it as SQL + Python on terabytes of data across 100 servers.

CORE IDEA — RDD (Resilient Distributed Dataset):
  Data is split into PARTITIONS spread across worker nodes.
  Every transformation is lazy — nothing runs until you call an action.

                  ┌─────────────────────────────────────┐
  Your code  →   │ Driver (your laptop / master node)  │
                  │   builds a DAG (execution plan)     │
                  └────────────┬────────────────────────┘
                               │ sends tasks
               ┌───────────────┼───────────────┐
          ┌────┴────┐     ┌────┴────┐     ┌────┴────┐
          │Worker 1 │     │Worker 2 │     │Worker 3 │
          │Partition│     │Partition│     │Partition│
          │  0,1    │     │  2,3    │     │  4,5    │
          └─────────┘     └─────────┘     └─────────┘

KEY CONCEPTS:
  Transformation  = lazy, returns new DataFrame (filter, select, groupBy)
  Action          = triggers computation, returns result (show, count, collect)
  Partition       = chunk of data processed on one worker
  Shuffle         = moving data between workers (expensive — minimize it)
  DAG             = directed acyclic graph of your transformations (execution plan)

Run locally:
  pip install pyspark
  python 01_basics.py

Run on cluster:
  docker-compose up -d
  docker exec spark-master spark-submit /opt/spark-apps/01_basics.py
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

# ─── 1. SparkSession — entry point to everything ──────────────────────────────
# In local mode: runs all tasks on your machine (good for learning)
# In cluster mode: driver talks to cluster manager

spark = SparkSession.builder \
    .appName("SparkBasics") \
    .master("local[*]") \
    .config("spark.sql.shuffle.partitions", "4")  \  # default is 200 — too high for small data
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")  # reduce noise
print("Spark version:", spark.version)

# ─── 2. Create DataFrame ──────────────────────────────────────────────────────
# DataFrame = distributed table (like pandas DataFrame but across many machines)

# From Python list
employees = spark.createDataFrame([
    (1, "Shubham", "Engineering", 95000.0),
    (2, "Alice",   "Engineering", 87000.0),
    (3, "Bob",     "Engineering", 87000.0),
    (4, "Carol",   "Marketing",   72000.0),
    (5, "Diana",   "Marketing",   68000.0),
    (6, "Eve",     "Marketing",   72000.0),
    (7, "Frank",   "HR",          65000.0),
    (8, "Grace",   "HR",          60000.0),
], schema=["id", "name", "dept", "salary"])

orders = spark.createDataFrame([
    (1, 1, "MacBook Pro",    2499.0, "delivered"),
    (2, 1, "AirPods",         199.0, "shipped"),
    (3, 2, "iPhone 15",      1199.0, "delivered"),
    (4, 3, "iPad Mini",       599.0, "pending"),
    (5, 3, "Apple Watch",     399.0, "cancelled"),
    (6, 4, "Magic Keyboard",  129.0, "delivered"),
], schema=["order_id", "emp_id", "product", "amount", "status"])

print("\n=== SCHEMA ===")
employees.printSchema()

# ─── 3. Basic transformations (LAZY — nothing runs yet) ───────────────────────
# select, filter, withColumn, drop, rename

print("\n=== SELECT & FILTER ===")
high_earners = employees \
    .select("name", "dept", "salary") \
    .filter(F.col("salary") >= 80000) \
    .orderBy(F.col("salary").desc())

high_earners.show()  # ← ACTION: triggers computation NOW

# withColumn: add or modify a column
enriched = employees.withColumn(
    "level",
    F.when(F.col("salary") >= 90000, "Senior")
     .when(F.col("salary") >= 75000, "Mid")
     .otherwise("Junior")
)
enriched.select("name", "dept", "salary", "level").show()

# ─── 4. Aggregations ─────────────────────────────────────────────────────────
print("\n=== GROUP BY ===")
dept_stats = employees.groupBy("dept").agg(
    F.count("*")              .alias("headcount"),
    F.avg("salary")           .alias("avg_salary"),
    F.max("salary")           .alias("max_salary"),
    F.sum("salary")           .alias("total_cost"),
    F.collect_list("name")    .alias("members"),      # like ARRAY_AGG
)
dept_stats.show(truncate=False)

# ─── 5. JOIN ──────────────────────────────────────────────────────────────────
print("\n=== JOIN ===")
emp_orders = employees.join(
    orders,
    employees["id"] == orders["emp_id"],
    how="left"               # left, right, inner, outer, semi, anti
)

emp_orders.select("name", "dept", "product", "amount", "status") \
    .orderBy("name") \
    .show()

# Total spend per employee (left join keeps employees with no orders)
spend = employees.join(orders, employees["id"] == orders["emp_id"], "left") \
    .groupBy("id", "name", "dept") \
    .agg(
        F.count("order_id")       .alias("order_count"),
        F.coalesce(               # SPARK coalesce = SQL COALESCE: first non-null
            F.sum("amount"), F.lit(0)
        )                         .alias("total_spent")
    ) \
    .orderBy(F.col("total_spent").desc())

spend.show()

# ─── 6. Window functions (same as SQL) ───────────────────────────────────────
print("\n=== WINDOW FUNCTIONS ===")
from pyspark.sql.window import Window

window_dept = Window.partitionBy("dept").orderBy(F.col("salary").desc())

ranked = employees.withColumn("rank",       F.rank()       .over(window_dept)) \
                  .withColumn("dense_rank", F.dense_rank() .over(window_dept)) \
                  .withColumn("row_num",    F.row_number()  .over(window_dept))

ranked.select("name", "dept", "salary", "rank", "dense_rank", "row_num") \
      .orderBy("dept", "rank") \
      .show()

# Running total within department
window_running = Window.partitionBy("dept") \
                       .orderBy("salary") \
                       .rowsBetween(Window.unboundedPreceding, Window.currentRow)

employees.withColumn(
    "running_total", F.sum("salary").over(window_running)
).select("name", "dept", "salary", "running_total") \
 .orderBy("dept", "salary") \
 .show()

# ─── 7. Read from files ───────────────────────────────────────────────────────
print("\n=== READING FILES ===")
import tempfile, os, json

# Write sample JSON files
tmp = tempfile.mkdtemp()
with open(os.path.join(tmp, "data.json"), "w") as f:
    for row in [{"city": "Mumbai", "pop": 20000000},
                {"city": "Delhi",  "pop": 32000000},
                {"city": "Bangalore", "pop": 12000000}]:
        f.write(json.dumps(row) + "\n")

cities = spark.read.json(tmp)
cities.show()

# ─── 8. SQL on DataFrames ─────────────────────────────────────────────────────
print("\n=== SPARK SQL ===")
employees.createOrReplaceTempView("employees")
orders.createOrReplaceTempView("orders")

result = spark.sql("""
    SELECT
        e.dept,
        COUNT(*)        AS headcount,
        AVG(e.salary)   AS avg_salary,
        SUM(o.amount)   AS total_revenue
    FROM employees e
    LEFT JOIN orders o ON e.id = o.emp_id
    GROUP BY e.dept
    ORDER BY total_revenue DESC NULLS LAST
""")
result.show()

print("\n=== KEY CONCEPTS ===")
print("""
  Transformation  (lazy, no compute):  select, filter, groupBy, join, withColumn
  Action         (triggers compute):   show, count, collect, write, take
  DataFrame      = distributed table with schema
  RDD            = lower-level distributed collection (use DataFrame instead)
  DAG            = Spark's execution plan — optimized by Catalyst optimizer
  Shuffle        = data moves between workers (groupBy, join) — most expensive op
""")

spark.stop()
