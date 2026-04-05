# Apache Spark — Basics, Partitions, Transformations

## What is Spark?

Distributed data processing — run SQL and computations on terabytes of data across hundreds of machines.

```
pandas:  runs on 1 machine, limited to RAM
Spark:   runs on 100 machines, handles petabytes
```

Think of it as: **SQL + Python, but distributed across a cluster.**

---

## Architecture

```
                ┌─────────────────────────────────────┐
Your code  →   │ Driver (your machine / master node)  │
                │   builds execution plan (DAG)        │
                └────────────┬────────────────────────┘
                             │ sends tasks to workers
           ┌─────────────────┼─────────────────┐
      ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
      │Worker 1 │       │Worker 2 │       │Worker 3 │
      │Partition│       │Partition│       │Partition│
      │  0, 1   │       │  2, 3   │       │  4, 5   │
      └─────────┘       └─────────┘       └─────────┘
```

---

## Core Concepts

| Concept | What it is |
| --- | --- |
| **DataFrame** | Distributed table with schema — like pandas but across machines |
| **Partition** | One chunk of data processed by one worker task |
| **Transformation** | Lazy operation — builds plan, runs nothing (filter, select, join) |
| **Action** | Triggers computation (show, count, collect, write) |
| **DAG** | Directed Acyclic Graph — Spark's optimized execution plan |
| **Shuffle** | Data moves between workers — most expensive operation |
| **Stage** | Group of tasks with no shuffle between them |
| **Cache** | Store DataFrame in memory to avoid recomputing |

---

## Lazy Evaluation — THE most important concept

```python
df = spark.read.parquet("data/")      # lazy — reads nothing
filtered = df.filter(col("age") > 25) # lazy — computes nothing
mapped = filtered.select("name","age") # lazy — computes nothing

count = mapped.count()                 # ACTION — runs entire plan NOW
```

Why lazy? Spark optimizes the full plan before running:
- Pushes filters early (scan less data)
- Combines multiple passes into one
- Reorders joins for best performance

---

## Partitions, coalesce, repartition

```python
df.rdd.getNumPartitions()       # see how many partitions

# coalesce(n) — reduce partitions, NO shuffle (fast)
df.coalesce(4)                  # merge partitions locally, no data movement
                                # use after filter, before write

# repartition(n) — change to n partitions, FULL shuffle (slower but even)
df.repartition(8)               # redistributes data evenly
                                # use before heavy join/groupBy on skewed data

# repartition by column — all same-key rows go to same partition
df.repartition("dept")          # groupBy("dept") after this = no shuffle!
```

### coalesce vs repartition

| | coalesce | repartition |
| --- | --- | --- |
| Shuffle | No (fast) | Yes (network cost) |
| Direction | Reduce only | Reduce or increase |
| Distribution | Uneven | Even |
| Use when | After filter, before write | Before join/groupBy on skewed data |

### Optimal partition size
- Target: **128MB per partition**
- Rule: 2–4 partitions per CPU core
- Too many → overhead, tiny files
- Too few → workers idle

---

## Common SQL COALESCE vs Spark coalesce

```sql
-- SQL: return first non-null value
SELECT COALESCE(SUM(amount), 0) FROM orders;
```

```python
# Spark DataFrame: same meaning
F.coalesce(F.sum("amount"), F.lit(0))

# Spark repartition method: COMPLETELY DIFFERENT — reduces partition count
df.coalesce(4)   # has nothing to do with null values
```

**Same word, different things.** SQL COALESCE = null handling. Spark `.coalesce()` = partition count.

---

## Files — learning order

| File | Covers |
| --- | --- |
| `01_basics.py` | SparkSession, DataFrame, select, filter, groupBy, join, window functions, SQL |
| `02_partitions.py` | Partitions, coalesce, repartition, skew, output files |
| `03_transformations_vs_actions.py` | Lazy eval, explode, cache, explain, DAG |

---

## Quick start

```bash
# Install locally
pip install pyspark

# Run any file
python 01_basics.py
python 02_partitions.py
python 03_transformations_vs_actions.py

# Spark UI while running
open http://localhost:4040

# Or with Docker cluster
docker-compose up -d
docker exec spark-master spark-submit /opt/spark-apps/01_basics.py
open http://localhost:8080   # cluster UI
```

---

## Cheat sheet

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("App").master("local[*]").getOrCreate()

# Read
df = spark.read.parquet("path/")
df = spark.read.csv("path/", header=True, inferSchema=True)
df = spark.read.json("path/")

# Transform (lazy)
df.select("a", "b")
df.filter(F.col("age") > 25)
df.withColumn("level", F.when(F.col("sal") > 90000, "Senior").otherwise("Junior"))
df.groupBy("dept").agg(F.avg("salary"), F.count("*"))
df.join(other, "id", "left")
df.orderBy(F.col("salary").desc())
df.coalesce(4)
df.repartition(8)
df.repartition("dept")

# Window
w = Window.partitionBy("dept").orderBy(F.col("salary").desc())
df.withColumn("rank", F.rank().over(w))
df.withColumn("lag", F.lag("revenue").over(w))
df.withColumn("running", F.sum("salary").over(w.rowsBetween(Window.unboundedPreceding, 0)))

# Actions (trigger compute)
df.show()
df.count()
df.collect()      # brings to driver — careful with large data
df.first()
df.take(10)
df.write.parquet("output/")

# Cache
df.cache()        # store in memory after first action
df.unpersist()    # free memory
```
