# Web Crawler — System Design (L6/L7)

## 1. Functional Requirements

| # | Requirement |
|---|-------------|
| 1 | Start crawling from seed URLs and recursively discover new URLs |
| 2 | Schedule crawls with configurable frequency per website type |
| 3 | Prioritize URLs — news > sports > static sites |
| 4 | Avoid duplicate URL crawling |
| 5 | Avoid storing duplicate content (even across different URLs) |
| 6 | Store raw HTML content and URL metadata |

---

## 2. Non-Functional Requirements

| # | Requirement |
|---|-------------|
| 1 | Scalable to billions of pages |
| 2 | Highly available — no single point of failure |
| 3 | Polite — respect robots.txt and crawl delays |
| 4 | Efficient bandwidth and storage usage |
| 5 | Low-latency DNS resolution via caching |

---

## 3. Capacity Planning

| Parameter | Value | Calculation |
|-----------|-------|-------------|
| Total pages | 1 billion | Target crawl size |
| Avg page size | 100 KB | Per page estimate |
| Total data/cycle | ~100 TB | 10^9 × 100 KB = 10^14 bytes = 100 TB |
| Daily data volume | ~14 TB/day | 100 TB ÷ 7 days |
| Bandwidth needed | ~160 MB/sec | 14 TB ÷ 86,400 sec ≈ 162 MB/sec |

---

## 4. System Components

| Component | Responsibility |
|-----------|---------------|
| Scheduler | Manages crawl schedule, priority, next crawl time per URL |
| Priority Queue | Holds URLs ordered by priority and scheduled time |
| DNS Resolver | Resolves URLs to IPs; caches results to reduce latency |
| Fetcher | Downloads HTML from resolved IP addresses |
| Extractor | Parses HTML, extracts new URLs, computes content checksums |
| SQL/NoSQL DB | Stores URL metadata (URL, priority, next crawl time) |
| Object Storage (S3) | Stores raw HTML/media content at petabyte scale |
| Checksum Store | Stores content hashes to detect duplicate pages |
| Bloom Filter | In-memory probabilistic structure for URL dedup checks |

---

## 5. Workflow

```
Seed URLs
    │
    ▼
Priority Queue
    │
    ▼
Scheduler ──── reads DB (next_crawl_time <= now) ──► re-queue
    │
    ▼
Worker Pool
    │
    ├─► DNS Resolver (cached) ──► IP address
    │
    ├─► Fetcher ──► raw HTML
    │
    └─► Extractor
            │
            ├─► Bloom Filter ──► URL seen? ──► YES → skip
            │                               └─► NO  → add to DB + queue
            │
            └─► Checksum (MD5/MurmurHash)
                    │
                    ├─► Duplicate content? ──► YES → discard
                    └─► Unique?            ──► NO  → store in S3
```

| Step | Action |
|------|--------|
| 1 | Seed URLs loaded into Priority Queue |
| 2 | Scheduler reads DB, pushes due URLs to queue by priority |
| 3 | Workers pull URLs from queue |
| 4 | DNS Resolver maps URL → IP (cached) |
| 5 | Fetcher downloads HTML page |
| 6 | Extractor parses HTML, extracts child URLs |
| 7 | Bloom Filter checks if URL already crawled |
| 8 | New URLs added to DB for future scheduling |
| 9 | Checksum computed → compared against Checksum Store |
| 10 | If unique → store in S3; if duplicate → discard |

---

## 6. Data Structures & Algorithms

| Structure | Purpose | Complexity |
|-----------|---------|------------|
| Priority Queue (Min Heap) | URL scheduling by priority + time | O(log n) insert/pop |
| Bloom Filter | Fast URL dedup check | O(1) lookup, ~0% false negatives |
| MD5 / MurmurHash | Content-level duplicate detection | O(1) hash comparison |
| SQL/NoSQL DB | URL metadata storage and querying | Indexed lookups |

---

## 7. Duplicate Detection Strategy

| Level | Method | How |
|-------|--------|-----|
| URL level | Bloom Filter | Check before adding URL to queue |
| Content level | MD5/MurmurHash checksum | Hash page content; compare with Checksum Store |

---

## 8. Politeness Policy

| Rule | Implementation |
|------|---------------|
| Respect robots.txt | Parse and honor crawl rules per domain |
| Crawl delay | Add delay between requests to same server |
| Per-domain page limit | Cap max pages crawled per domain |
| Threshold stops | Halt crawling domain if limit breached |

---

## 9. Recrawling Logic

| Website Type | Crawl Frequency |
|-------------|----------------|
| News sites | High (hourly / daily) |
| Sports sites | Medium (daily) |
| Static/corporate sites | Low (weekly / monthly) |

Scheduler queries DB for URLs where `next_crawl_time <= now` and re-queues them.

---

## 10. Security & Attack Mitigation

| Attack | Mitigation |
|--------|-----------|
| Crawl explosion | Per-domain page cap + robots.txt crawl-delay |
| Infinite redirect loops | Max redirect depth limit |
| Malicious content | Sanitize and validate fetched HTML before processing |

---

## Files in this folder

```
README.md           ← this file (requirements, capacity, workflow, HLD, Q&A)
hld.md              ← High Level Design (component diagram, tech choices)
lld.md              ← Low Level Design (DB schema, class design, APIs)
notes_deep_dive.md  ← Q&A deep dives (Cassandra vs MySQL, DNS TTL, Kafka priority)
code/
  crawler.py        ← runnable POC (Scheduler, PriorityQueue, BloomFilter, Fetcher)
```

---

## Q&A — Interview Deep Dives

### Q: How is 200 bytes per URL calculated?

```
Each URL row in the DB stores:
  url          TEXT  → avg 80 bytes  (https://cnn.com/article/some-long-title)
  domain       TEXT  → avg 20 bytes  (cnn.com)
  status       TEXT  → 10 bytes      (pending/crawling/done)
  next_crawl   TIMESTAMP → 8 bytes
  last_crawled TIMESTAMP → 8 bytes
  crawl_count  INT   → 4 bytes
  url_id       UUID  → 16 bytes
  overhead (Cassandra row metadata) → ~50 bytes
  ─────────────────────────────────────────────
  Total ≈ 200 bytes per URL

1 billion URLs × 200 bytes = 200 GB
Redis stores everything in RAM → $200GB RAM is very expensive
Cassandra stores on disk → $200 GB disk is cheap ($10/month on AWS)
```

### Q: Why Cassandra over MySQL/Redis/DynamoDB?

```
Option          Why NOT                              Why YES (Cassandra)
──────────────────────────────────────────────────────────────────────────
MySQL           Single write master → bottleneck     —
                Sharding is manual and painful
                JOINs not needed here

Redis           All data in RAM → too expensive       Good for DNS cache (small)
                No complex queries                    NOT for URL DB (billions of rows)
                TTL-based — URLs need permanent store

DynamoDB        Good option! AWS-managed, scalable   Cassandra: open source, no vendor lock
                But vendor lock-in to AWS            Self-host or use DataStax

PostgreSQL      Better than MySQL (partitioning)     OK for <100M URLs
                But still single-master writes        Cassandra wins at billion scale

Cassandra ✅    Distributed writes (no master)
                Partition key = domain → locality
                Cheap disk storage
                Linear scaling (add nodes)
                CQL query: WHERE domain=? AND next_crawl_at <= now()
```

### Q: How does Scheduler run every minute?

```
Production:   Kubernetes CronJob   → schedule: "* * * * *"
Dev/POC:      APScheduler (Python) → @scheduler.scheduled_job('interval', minutes=1)
Simplest:     while True: run(); time.sleep(60)

Optimizations (don't scan 1B rows every minute):
  1. Partition by crawl_date → only query today's bucket (tiny scan)
  2. Event-driven → after crawl, emit delayed Kafka event for next crawl time
  3. Separate schedulers per tier: news=hourly, sports=daily, static=weekly
```

### Q: Why Kafka as Priority Queue? Limitations?

```
Kafka is FIFO per partition — NOT a true priority queue.

Solution: Separate topics per priority tier
  Topic: crawler-priority-1-news    ← workers poll this first
  Topic: crawler-priority-2-sports
  Topic: crawler-priority-3-static  ← polled last

Workers: weighted round-robin (5 news : 2 sports : 1 static per round)
  → prevents starvation of lower-priority queues

Alternative: Redis Sorted Set (true priority)
  ZADD queue 1.0 "url"   → ZPOPMIN always returns lowest score (highest priority)
  Combine: Kafka (durable store) + Redis Sorted Set (priority routing)
```

### Q: Kafka alternatives comparison

See: `learning-journal/09-kafka/05_kafka_alternatives.py`

### Q: K8s CronJob for Scheduler — see POC

See: `learning-journal/03-docker-k8s/06_k8s_poc.py`
