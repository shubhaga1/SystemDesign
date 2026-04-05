"""
PARTITIONS, COALESCE & REPARTITION

This is the MOST IMPORTANT concept for Spark performance.

PARTITION = one chunk of data processed by one task on one worker
  More partitions = more parallelism (up to number of CPU cores)
  Too few partitions = workers idle
  Too many partitions = overhead dominates

  ┌──────────────────────────────────────────────────────────┐
  │                  DataFrame (1 million rows)              │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
  │  │Partition0│  │Partition1│  │Partition2│  │Part..3 │  │
  │  │ 250K rows│  │ 250K rows│  │ 250K rows│  │250K row│  │
  │  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
  │   Worker 1      Worker 2      Worker 3      Worker 4    │
  └──────────────────────────────────────────────────────────┘

coalesce(n):
  Reduce partitions to n — NO shuffle (fast)
  Merges existing partitions, never moves data between workers
  Use to: reduce small files after filter, before write

repartition(n):
  Change to exactly n partitions — FULL shuffle (slow but uniform)
  Redistributes data evenly across all workers
  Use to: fix skew, increase parallelism before heavy joins

Run: python 02_partitions.py
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
import time

spark = SparkSession.builder \
    .appName("Partitions") \
    .master("local[4]") \
    .config("spark.sql.shuffle.partitions", "8") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# ─── 1. See current partitions ────────────────────────────────────────────────
print("=== 1. PARTITION COUNT ===")

df = spark.range(1_000_000)  # creates 1M rows quickly
print(f"Default partitions: {df.rdd.getNumPartitions()}")
# local[4] = 4 CPU cores = 4 default partitions

# ─── 2. Generating data with skew ─────────────────────────────────────────────
print("\n=== 2. DATA SKEW EXAMPLE ===")
# Skew = one partition has WAY more data than others → one slow task stalls entire job

data = (
    [(i, "Engineering") for i in range(100000)] +  # 100K Engineering rows
    [(i, "HR")          for i in range(100)]    +  # 100 HR rows
    [(i, "Marketing")   for i in range(500)]       # 500 Marketing rows
)
skewed = spark.createDataFrame(data, ["id", "dept"])

print("Partition sizes (before repartition):")
skewed.groupBy(F.spark_partition_id().alias("partition_id")) \
      .count() \
      .orderBy("partition_id") \
      .show()

# ─── 3. repartition(n) — full shuffle, even distribution ─────────────────────
print("\n=== 3. repartition(n) — even distribution ===")
print("""
  repartition(n):
    → Triggers a FULL SHUFFLE (all data moves across network)
    → Every partition gets roughly equal rows
    → Use before heavy joins or aggregations on skewed data
    → Expensive: O(n) data movement
""")

evenly_split = skewed.repartition(4)

print("Partition sizes (after repartition(4)):")
evenly_split.groupBy(F.spark_partition_id().alias("partition_id")) \
            .count() \
            .orderBy("partition_id") \
            .show()

# ─── 4. repartition by column — co-locate related data ───────────────────────
print("\n=== 4. repartition BY COLUMN — co-locate data ===")
print("""
  repartition("dept"):
    All rows with same dept → same partition
    Benefit: groupBy("dept") after this = NO shuffle needed
    Use before: multiple operations on same key
""")

by_dept = skewed.repartition("dept")
print(f"Partitions after repartition('dept'): {by_dept.rdd.getNumPartitions()}")
# default shuffle partitions = 8, so 8 partitions

by_dept.groupBy("dept", F.spark_partition_id().alias("part_id")) \
       .count() \
       .orderBy("dept") \
       .show()

# ─── 5. coalesce(n) — reduce partitions, NO shuffle ──────────────────────────
print("\n=== 5. coalesce(n) — shrink partitions without shuffle ===")
print("""
  coalesce(n):
    → NO shuffle — just merges existing partitions (fast!)
    → Can only REDUCE partitions (not increase)
    → Use: after filter removes most data, before writing to fewer files
    → Result: some partitions may be larger than others (not perfectly even)

  WHY: after a heavy filter, you might have 200 partitions with 10 rows each
       → 200 tiny files on disk → slow reads later
       → coalesce(4) merges them into 4 files without any network transfer
""")

large_df = spark.range(1_000_000).repartition(100)
print(f"Before coalesce: {large_df.rdd.getNumPartitions()} partitions")

after_filter = large_df.filter(F.col("id") < 10000)   # 99% of data filtered out
print(f"After filter (still {after_filter.rdd.getNumPartitions()} partitions, mostly empty)")

coalesced = after_filter.coalesce(4)
print(f"After coalesce(4): {coalesced.rdd.getNumPartitions()} partitions")

print("\nPartition sizes after coalesce:")
coalesced.groupBy(F.spark_partition_id().alias("part")) \
         .count() \
         .orderBy("part") \
         .show()

# ─── 6. coalesce vs repartition side by side ─────────────────────────────────
print("\n=== 6. COALESCE vs REPARTITION — comparison ===")
print("""
  ┌─────────────────┬──────────────────────────┬──────────────────────────┐
  │                 │ coalesce(n)              │ repartition(n)           │
  ├─────────────────┼──────────────────────────┼──────────────────────────┤
  │ Shuffle         │ NO  (fast)               │ YES (slow, network cost) │
  │ Direction       │ reduce only              │ reduce OR increase       │
  │ Distribution    │ uneven (merges adjacent) │ even (hash distributed)  │
  │ Use case        │ after filter, before write│ before join/groupBy     │
  │ Cost            │ cheap                    │ expensive                │
  └─────────────────┴──────────────────────────┴──────────────────────────┘
""")

# ─── 7. Optimal partition size rule ──────────────────────────────────────────
print("=== 7. OPTIMAL PARTITION SIZE ===")
print("""
  Target: 128MB per partition (Spark default recommendation)

  Too few partitions:
    Workers sit idle, one big task runs on one core
    → repartition(more) before heavy operation

  Too many partitions:
    Scheduler overhead, too many tiny files written to disk
    → coalesce(fewer) before write

  Rule of thumb:
    2-4 partitions per CPU core in the cluster
    For files: 128MB per partition
    Default shuffle partitions = 200 (set lower for small data):
      spark.conf.set("spark.sql.shuffle.partitions", "8")

  Check partition sizes:
    df.rdd.getNumPartitions()
    df.groupBy(spark_partition_id()).count().show()
""")

# ─── 8. Writing — how partitions affect output files ─────────────────────────
print("=== 8. HOW PARTITIONS AFFECT OUTPUT FILES ===")
print("""
  spark.write.parquet("output/")  →  creates ONE FILE PER PARTITION

  If you have 200 partitions → 200 parquet files
  Reading later: 200 file-open operations = slow

  ALWAYS coalesce/repartition before writing:
    df.coalesce(4).write.parquet("output/")     → 4 files (good for small data)
    df.repartition(50).write.parquet("output/") → 50 files (good for large data)

  Partition by column (like Hive partitioning):
    df.write.partitionBy("year", "month").parquet("output/")
    → output/year=2026/month=01/file.parquet
    → reads for Jan 2026 only scan one folder = partition pruning
""")

spark.stop()
