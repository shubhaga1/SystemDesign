# Web Crawler — High Level Design (HLD)

## Architecture Diagram

```
                        ┌─────────────────────────────────────────────┐
                        │              CONTROL PLANE                   │
                        │                                             │
                        │   ┌───────────┐      ┌──────────────────┐  │
                        │   │ Scheduler │─────►│  Priority Queue  │  │
                        │   │           │      │  (Kafka / Redis) │  │
                        │   └─────┬─────┘      └────────┬─────────┘  │
                        │         │                     │             │
                        │   reads │ next_crawl_time     │ pop URL     │
                        │         ▼                     ▼             │
                        │   ┌──────────┐       ┌───────────────┐     │
                        │   │ URL DB   │       │  Worker Pool  │     │
                        │   │(Postgres/│       │  (N machines) │     │
                        │   │ Cassandra│       └──────┬────────┘     │
                        │   └──────────┘              │              │
                        └────────────────────────────────────────────┘
                                                       │
                    ┌──────────────────────────────────┤
                    │                                  │
                    ▼                                  ▼
           ┌──────────────┐                  ┌──────────────────┐
           │ DNS Resolver │                  │    Fetcher       │
           │  (cached,    │──── IP ─────────►│  (HTTP client)   │
           │   Redis TTL) │                  └────────┬─────────┘
           └──────────────┘                           │ raw HTML
                                                      ▼
                                            ┌──────────────────┐
                                            │    Extractor     │
                                            │  (HTML parser)   │
                                            └───┬──────────┬───┘
                                                │          │
                              ┌─────────────────┘          └─────────────────┐
                              ▼                                               ▼
                    ┌──────────────────┐                         ┌──────────────────┐
                    │  URL Dedup       │                         │  Content Dedup   │
                    │  Bloom Filter    │                         │  MD5 Checksum    │
                    │  (Redis / mem)   │                         │  Store (Redis)   │
                    └────────┬─────────┘                         └────────┬─────────┘
                             │ new URL?                                   │ unique?
                             ▼                                            ▼
                    ┌──────────────────┐                         ┌──────────────────┐
                    │   URL DB         │                         │   Object Store   │
                    │   (schedule      │                         │   S3 / GCS       │
                    │    next crawl)   │                         │   (raw HTML)     │
                    └──────────────────┘                         └──────────────────┘
```

---

## Component Decisions

### Priority Queue
```
Options:   Kafka, Redis Sorted Set, RabbitMQ
Choice:    Kafka
Why:       - handles millions of URL messages per second
           - durable (messages survive restarts)
           - partitioned by domain → politeness (one partition per domain)
           - consumers (workers) scale independently
```

### URL Database
```
Options:   PostgreSQL, Cassandra, DynamoDB
Choice:    Cassandra
Why:       - billions of URL rows
           - write-heavy (new URLs discovered constantly)
           - partition key = domain → locality
           - no joins needed (simple key-value access pattern)

Schema:
  url_id       UUID
  url          TEXT
  domain       TEXT
  priority     INT        (1=news, 2=sports, 3=static)
  status       TEXT       (pending, crawling, done, failed)
  next_crawl   TIMESTAMP
  last_crawled TIMESTAMP
  crawl_count  INT
```

### DNS Resolver
```
Options:   System DNS, Custom caching layer
Choice:    Redis-backed DNS cache
Why:       - DNS lookup = 50-100ms each time
           - same domain crawled thousands of times
           - cache IP per domain with TTL (300s)
           - reduces latency, reduces load on DNS servers
```

### Fetcher
```
Options:   Single-threaded, Multi-threaded, Async
Choice:    Async (Python asyncio / Go goroutines)
Why:       - fetching is I/O bound (waiting for HTTP response)
           - async: 1 thread handles 10,000 concurrent HTTP requests
           - vs 10,000 threads: too much memory, context-switch overhead
```

### Content Storage
```
Options:   File system, HDFS, S3
Choice:    S3 / GCS
Why:       - petabyte scale (10 PB per crawl cycle)
           - cheap ($0.023/GB vs $0.10/GB for EBS)
           - durable (11 nines)
           - decoupled from compute
```

### Bloom Filter
```
What:      Probabilistic data structure
           - asks "have I seen this URL?"
           - 0% false negatives (never says "not seen" when it has been)
           - small false positive rate (~1%) → occasionally re-crawl a URL (acceptable)
           - uses bits, not full URLs → 1 billion URLs ≈ 1.2 GB RAM

Options:   In-memory per worker, Redis Bloom (shared)
Choice:    Redis Bloom Filter (shared across all workers)
Why:       - workers are stateless, can scale up/down
           - shared state prevents race conditions
```

---

## Scaling Strategy

```
Bottleneck          Solution
─────────────────────────────────────────────────────
Too many URLs       Scale worker pool horizontally (add machines)
DNS slow            Redis DNS cache with TTL
DB write contention Cassandra (distributed writes, no locks)
Queue backlog       Add Kafka partitions + more consumer workers
S3 write throughput S3 handles millions of writes/sec natively
Single point failure All components stateless → restart anytime
                    Kafka durable → no message loss on crash
```

---

## Tech Stack Summary

| Component | Technology |
|-----------|-----------|
| Priority Queue | Apache Kafka |
| URL Database | Apache Cassandra |
| DNS Cache | Redis |
| URL Dedup | Redis Bloom Filter |
| Content Dedup | Redis (MD5 hash → URL mapping) |
| Fetcher | Python asyncio / aiohttp |
| HTML Parser | BeautifulSoup / lxml |
| Object Storage | AWS S3 |
| Scheduler | Cron job / Kubernetes CronJob |
| Monitoring | Prometheus + Grafana |
