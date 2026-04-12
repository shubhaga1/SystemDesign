# Web Crawler — Deep Dive Q&A

---

## Q1. Why Cassandra for URL DB? Why not MySQL or Redis?

### The access pattern decides the DB

```
What we do with the URL DB:
  WRITE: billions of new URLs discovered constantly (write-heavy)
  READ:  "give me all URLs where next_crawl_at <= now()"
  UPDATE: status=done, update next_crawl_at after each crawl
```

### Why NOT MySQL?
```
MySQL = single master for writes
  → All writes go to ONE machine
  → 1 billion URLs, millions of new URLs/hour → master is bottleneck
  → Need to shard manually → complex, painful

Cassandra = no master, distributed writes
  → Every node accepts writes
  → Add more nodes → linear write scaling
  → Partition key = domain → all URLs for a domain land on same node
```

### Why NOT Redis for URL DB?
```
Redis = in-memory store
  → 1 billion URLs × 200 bytes each = 200 GB RAM → too expensive
  → Redis is for CACHE (temporary, fast, small)
  → No complex queries ("give me URLs due for crawl")
  → No persistence guarantee by default

Cassandra = disk-based, durable, cheap
  → 1 billion rows = terabytes → fine on disk
  → Survives restarts (writes to disk)
  → CQL: SELECT * WHERE domain=? AND next_crawl_at <= ?
```

### Cassandra Schema
```sql
CREATE TABLE url_metadata (
    domain        TEXT,
    next_crawl_at TIMESTAMP,
    url_id        UUID,
    url           TEXT,
    status        TEXT,
    PRIMARY KEY (domain, next_crawl_at, url_id)
) WITH CLUSTERING ORDER BY (next_crawl_at ASC);

-- Query: "give me URLs in domain cnn.com due for crawl"
SELECT * FROM url_metadata
WHERE domain = 'cnn.com' AND next_crawl_at <= toTimestamp(now());
```

---

## Q2. Why DNS TTL = 5 minutes? Not longer?

```
DNS TTL = how long we trust the cached IP before re-checking

DNS Cache stores:  cnn.com → 192.168.1.5 (expires in 5 min)
```

### Why not cache forever?
```
IP addresses CHANGE:
  - CDN (Cloudflare/Akamai) rotates IPs for load balancing
  - Server migration → domain points to new IP
  - If cached forever → we keep hitting old IP → connection refused

5 minutes (300s) is the standard DNS TTL for most websites.
Some are shorter (60s for high-availability sites), some longer (3600s for static).
We use 300s as a safe middle ground.
```

### Why cache at all?
```
DNS lookup = 50-100ms each time (goes to DNS server over network)
Same domain crawled 10,000 times → 10,000 × 50ms = 500 seconds wasted
With cache → only 1 DNS lookup per 5 minutes per domain → 99% time saved
```

---

## Q3. How does the Scheduler run every minute? Which scheduler?

### Option 1 — Kubernetes CronJob (production)
```yaml
# runs every minute
apiVersion: batch/v1
kind: CronJob
metadata:
  name: crawler-scheduler
spec:
  schedule: "* * * * *"    # every minute (cron syntax)
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: scheduler
            image: crawler-scheduler:latest
            command: ["python", "scheduler.py"]
```
```
* * * * *  = minute hour day month weekday
* = any value
So * * * * * = every minute of every hour of every day
```

### Option 2 — APScheduler (Python, in-process)
```python
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', minutes=1)
def run_scheduler():
    due_urls = db.query("SELECT * FROM url_metadata WHERE next_crawl_at <= now()")
    for url in due_urls:
        kafka_producer.send('crawler-queue', url)

scheduler.start()
```

### Option 3 — Simple loop (POC)
```python
import time
while True:
    enqueue_due_urls()
    time.sleep(60)
```

### How to OPTIMIZE the scheduler (not run every minute blindly)?

**Problem:** 1 billion URLs — querying every minute = full table scan = slow.

**Optimization 1 — Partition by time bucket**
```
Instead of scanning all URLs, only query today's bucket:
  Partition key = (domain, crawl_date)
  Only query crawl_date = today → much smaller scan
```

**Optimization 2 — Event-driven (no polling)**
```
Don't run every minute. Instead:
  After crawling a URL → compute next_crawl_at → set a timer event in Kafka.
  Kafka Streams / Flink can delay-emit the message at the right time.
  → Zero polling, zero wasted queries.
```

**Optimization 3 — Priority tiers, not one scheduler**
```
News scheduler    → runs every 1 hour   (small set of URLs)
Sports scheduler  → runs every 24 hours
Static scheduler  → runs every 7 days

Each tier is a separate CronJob with its own schedule.
Much smaller query per run.
```

---

## Q4. Why Kafka as Priority Queue? (and its limitations)

### What Kafka IS good at
```
- Durable: messages survive crashes (written to disk)
- Scalable: millions of messages/sec
- Decoupled: producers and consumers are independent
- Replayable: consumers can re-read old messages
- Partitioned: parallelism by domain
```

### What Kafka is NOT good at (the honest truth)
```
Kafka is NOT a true priority queue.
- Kafka partitions are FIFO (ordered log) — no global ordering across partitions
- You cannot say "process news before sports" globally across Kafka
- Kafka has no built-in priority — it processes messages in offset order

So how do we fake priority in Kafka?
```

### Kafka Priority Simulation — 3 approaches

**Approach 1 — Separate topics per priority tier (simplest)**
```
Topic: crawler-priority-1    ← news (workers poll this first)
Topic: crawler-priority-2    ← sports
Topic: crawler-priority-3    ← static (workers poll this last)

Workers poll in order:
  while true:
    url = poll(priority-1 topic)   # check news first
    if empty: url = poll(priority-2)
    if empty: url = poll(priority-3)
    crawl(url)

Pros: simple, works well in practice
Cons: if news queue is always full, sports/static starve
Fix:  weighted polling (process 5 news per 2 sports per 1 static)
```

**Approach 2 — Priority field in message + weighted consumer**
```
Message: { "url": "...", "priority": 1, "domain_type": "news" }
Consumer reads batch → sorts by priority → processes highest first
Works within a batch, not globally
```

**Approach 3 — Separate Kafka cluster + Redis PQ hybrid**
```
Kafka: durable message storage (all URLs go here)
Redis Sorted Set: real priority queue (score = priority × timestamp)

ZADD crawler-queue 1.0 "https://cnn.com"    # news, score=1
ZADD crawler-queue 2.0 "https://espn.com"   # sports, score=2
ZPOPMIN crawler-queue                        # always gets lowest score (highest priority)
```
