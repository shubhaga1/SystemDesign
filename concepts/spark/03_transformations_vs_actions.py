"""
TRANSFORMATIONS vs ACTIONS — Lazy Evaluation

KEY INSIGHT:
  Spark does NOTHING until you call an action.
  Transformations just build a recipe (DAG).
  Action = cook the recipe = actual computation.

  WHY LAZY?
    Spark can optimize the entire plan before running:
    - Push filters down (scan less data)
    - Combine multiple maps into one pass
    - Avoid materializing intermediate results

  Transformation:  filter, select, map, groupBy, join, withColumn
  Action:          show, count, collect, write, take, first, save

Run: python 03_transformations_vs_actions.py
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import time

spark = SparkSession.builder \
    .appName("LazyEval") \
    .master("local[*]") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ─── 1. Lazy evaluation demo ──────────────────────────────────────────────────
print("=== 1. LAZY EVALUATION — nothing runs until action ===")

t0 = time.time()

# These lines execute INSTANTLY — no data processed yet
df = spark.range(10_000_000)
filtered   = df.filter(F.col("id") > 5_000_000)    # lazy
mapped     = filtered.withColumn("doubled", F.col("id") * 2)  # lazy
aggregated = mapped.groupBy(F.col("id") % 100).count()        # lazy

print(f"Built DAG in {time.time()-t0:.3f}s  ← instant, nothing computed yet")

# count() is an ACTION — triggers execution of the entire DAG
t1 = time.time()
result_count = aggregated.count()
print(f"Action count()  completed in {time.time()-t1:.3f}s  ← actual computation")
print(f"Result: {result_count} groups")

# ─── 2. Common transformations ───────────────────────────────────────────────
print("\n=== 2. TRANSFORMATIONS (all lazy) ===")

data = spark.createDataFrame([
    (1, "Alice",   "Engineering", 87000, ["Python","Java"]),
    (2, "Bob",     "Engineering", 85000, ["Scala","Spark"]),
    (3, "Carol",   "Marketing",   72000, ["Excel","SQL"]),
    (4, "Diana",   "HR",          65000, ["HRIS"]),
    (5, "Eve",     "Engineering", 92000, ["Python","ML","Spark"]),
], ["id", "name", "dept", "salary", "skills"])

# select — pick columns, rename, compute
data.select(
    "name",
    F.upper("dept").alias("dept_upper"),
    (F.col("salary") / 1000).alias("salary_k"),
    F.size("skills").alias("skill_count")
).show()

# filter / where — same thing
data.filter(
    (F.col("dept") == "Engineering") & (F.col("salary") > 86000)
).show()

# withColumn — add or replace a column
data.withColumn("bonus", F.col("salary") * 0.1) \
    .withColumn("total_comp", F.col("salary") + F.col("bonus")) \
    .select("name", "salary", "bonus", "total_comp") \
    .show()

# ─── 3. explode — flatten arrays ─────────────────────────────────────────────
print("\n=== 3. EXPLODE — flatten array column ===")
# One row per skill (like UNNEST in SQL)
data.withColumn("skill", F.explode("skills")) \
    .select("name", "dept", "skill") \
    .show()

# ─── 4. distinct, dropDuplicates ─────────────────────────────────────────────
print("\n=== 4. DISTINCT & DEDUPLICATION ===")
data.select("dept").distinct().show()                        # unique depts
data.dropDuplicates(["dept"]).select("dept", "name").show() # keep first row per dept

# ─── 5. union, intersect, subtract ───────────────────────────────────────────
print("\n=== 5. SET OPERATIONS ===")
eng = data.filter(F.col("dept") == "Engineering").select("name")
high = data.filter(F.col("salary") > 85000).select("name")

print("Engineering:")
eng.show()
print("High salary (>85K):")
high.show()
print("Union (all):")
eng.union(high).distinct().show()
print("Intersect (both):")
eng.intersect(high).show()
print("Subtract (eng but NOT high salary):")
eng.subtract(high).show()

# ─── 6. Actions ───────────────────────────────────────────────────────────────
print("\n=== 6. ACTIONS (trigger computation) ===")

# count — number of rows
print("count():", data.count())

# collect — bring all data to driver (DANGEROUS for large datasets)
rows = data.select("name", "salary").collect()
print("collect() first row:", rows[0])
# rows is now a Python list on the driver — no longer distributed

# take(n) — collect first n rows
print("take(2):", data.take(2))

# first() — first row
print("first():", data.first())

# show(n) — print n rows (default 20)
data.select("name", "dept").show(3)

# ─── 7. Cache — avoid recomputing ────────────────────────────────────────────
print("\n=== 7. CACHE — avoid recomputing expensive transforms ===")
print("""
  Without cache: every action re-runs the entire DAG from scratch
  With cache:    first action computes and stores in memory
                 subsequent actions read from cache

  Use when:
    You use the same DataFrame multiple times
    The DataFrame is expensive to compute (joins, aggregations)

  Levels:
    .cache()                     = MEMORY_AND_DISK (default)
    .persist(StorageLevel.MEMORY_ONLY)
    .persist(StorageLevel.DISK_ONLY)
""")

expensive = data \
    .filter(F.col("salary") > 70000) \
    .withColumn("bonus", F.col("salary") * 0.1)

expensive.cache()          # marks for caching — not yet materialized

# First action: computes + stores in cache
t1 = time.time()
c1 = expensive.count()
print(f"First count (compute + cache): {time.time()-t1:.3f}s  → {c1}")

# Second action: reads from cache
t2 = time.time()
c2 = expensive.count()
print(f"Second count (from cache):     {time.time()-t2:.3f}s  → {c2}")

expensive.unpersist()      # free cache memory when done

# ─── 8. DAG visualization ────────────────────────────────────────────────────
print("\n=== 8. HOW SPARK PLANS YOUR QUERY ===")
print("""
  Every Spark job = DAG (Directed Acyclic Graph) of stages
  Spark UI (localhost:4040) shows the DAG while job runs

  STAGE = set of tasks with no shuffle between them
  TASK  = one unit of work on one partition on one worker

  Example DAG:
    Stage 1: read file → filter → map  (no shuffle between these)
             ↓
         [SHUFFLE BOUNDARY — groupBy causes data movement]
             ↓
    Stage 2: aggregate each partition → final merge

  To see the plan:
    df.explain()              → show logical + physical plan
    df.explain("extended")   → show all 4 plans
""")

data.groupBy("dept").agg(F.avg("salary")).explain()

spark.stop()
