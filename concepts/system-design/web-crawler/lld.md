# Web Crawler — Low Level Design (LLD)

## Class Design

```
┌──────────────────────────────────────────────────────────────┐
│                        CrawlerSystem                         │
│                                                              │
│  + scheduler: Scheduler                                      │
│  + workerPool: WorkerPool                                    │
│  + urlDB: UrlRepository                                      │
│  + storage: ContentStorage                                   │
│  + start(seedUrls: List[str])                                │
└──────────────────────────────────────────────────────────────┘
         │               │               │
         ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
│  Scheduler   │ │  WorkerPool  │ │  UrlRepository   │
│              │ │              │ │                  │
│ +schedule()  │ │ +workers[]   │ │ +save(url)       │
│ +requeue()   │ │ +dispatch()  │ │ +getDue()        │
│              │ │              │ │ +updateStatus()  │
└──────┬───────┘ └──────┬───────┘ └──────────────────┘
       │                │
       ▼                ▼
┌──────────────┐ ┌──────────────────────────────────────────┐
│PriorityQueue │ │               Worker                     │
│              │ │                                          │
│ +push(url)   │ │ +dnsResolver: DnsResolver                │
│ +pop()       │ │ +fetcher: Fetcher                        │
└──────────────┘ │ +extractor: Extractor                    │
                 │ +bloomFilter: BloomFilter                 │
                 │ +checksumStore: ChecksumStore             │
                 │ +contentStorage: ContentStorage           │
                 │                                          │
                 │ +process(url: UrlTask)                   │
                 └──────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┬──────────────┐
          ▼              ▼              ▼              ▼
  ┌─────────────┐ ┌───────────┐ ┌──────────────┐ ┌──────────────┐
  │ DnsResolver │ │  Fetcher  │ │  Extractor   │ │BloomFilter   │
  │             │ │           │ │              │ │              │
  │ +resolve(   │ │ +fetch(   │ │ +extractUrls │ │ +contains(   │
  │   domain)   │ │   ip,url) │ │   (html)     │ │   url)       │
  │ cache: Redis│ │ timeout   │ │ +checksum(   │ │ +add(url)    │
  └─────────────┘ │ retries   │ │   html)      │ └──────────────┘
                  └───────────┘ └──────────────┘
```

---

## Database Schema

### url_metadata (Cassandra)
```sql
CREATE TABLE url_metadata (
    domain          TEXT,
    url_id          UUID,
    url             TEXT,
    priority        INT,       -- 1=news, 2=sports, 3=static
    status          TEXT,      -- pending | crawling | done | failed
    next_crawl_at   TIMESTAMP,
    last_crawled_at TIMESTAMP,
    crawl_count     INT,
    fail_count      INT,
    robots_txt_url  TEXT,
    PRIMARY KEY (domain, next_crawl_at, url_id)
) WITH CLUSTERING ORDER BY (next_crawl_at ASC);

-- Query: get all URLs due for crawl in a domain
-- SELECT * FROM url_metadata WHERE domain=? AND next_crawl_at <= now()
```

### content_checksums (Redis)
```
Key:   checksum:<md5_hash>
Value: s3_path (e.g. "s3://crawl-bucket/2025/11/abc123.html")
TTL:   none (permanent)

Purpose: detect duplicate content across different URLs
```

### dns_cache (Redis)
```
Key:   dns:<domain>
Value: <ip_address>
TTL:   300 seconds

Purpose: avoid repeated DNS lookups for same domain
```

---

## API Design (Internal REST)

### Scheduler API
```
POST /scheduler/seed
Body: { "urls": ["https://cnn.com", "https://bbc.com"] }
Response: { "queued": 2 }

GET /scheduler/stats
Response: { "pending": 1000000, "crawling": 500, "done": 50000000 }
```

### Worker API
```
POST /worker/crawl
Body: { "url": "https://cnn.com/article/1", "priority": 1 }
Response: { "status": "queued" }

GET /worker/health
Response: { "status": "ok", "active_jobs": 42 }
```

---

## URL Priority Scoring

```python
def compute_priority(url: str, domain_type: str, last_crawled: datetime) -> int:
    base_score = {
        "news":   1,    # highest priority
        "sports": 2,
        "static": 3,    # lowest priority
    }.get(domain_type, 3)

    # Boost if not crawled recently
    hours_since_crawl = (now() - last_crawled).hours
    freshness_boost = 0 if hours_since_crawl < 1 else -1   # lower = higher priority

    return base_score + freshness_boost
```

---

## Recrawl Schedule

```python
def next_crawl_time(domain_type: str, fail_count: int) -> datetime:
    base_intervals = {
        "news":   timedelta(hours=1),
        "sports": timedelta(hours=24),
        "static": timedelta(days=7),
    }
    interval = base_intervals.get(domain_type, timedelta(days=7))

    # Exponential backoff on failures
    if fail_count > 0:
        interval = interval * (2 ** min(fail_count, 5))  # max 32x backoff

    return now() + interval
```

---

## Bloom Filter Sizing

```
Target:   1 billion URLs
FP rate:  1% (acceptable — occasional re-crawl)
Formula:  m = -n * ln(p) / (ln(2))^2
          m = -1B * ln(0.01) / 0.48
          m ≈ 9.6 billion bits ≈ 1.2 GB

Hash functions: k = (m/n) * ln(2) ≈ 7

Conclusion: 1.2 GB RAM for 1 billion URLs — very efficient
```

---

## Politeness — Rate Limiter per Domain

```python
class DomainRateLimiter:
    """
    Token bucket per domain.
    Ensures we don't hammer one server.
    """
    def __init__(self, requests_per_second: float = 1.0):
        self.rate = requests_per_second
        self.tokens: Dict[str, float] = defaultdict(float)
        self.last_check: Dict[str, datetime] = {}

    def can_crawl(self, domain: str) -> bool:
        now = time.time()
        elapsed = now - self.last_check.get(domain, now)
        self.tokens[domain] = min(1.0, self.tokens[domain] + elapsed * self.rate)
        self.last_check[domain] = now

        if self.tokens[domain] >= 1.0:
            self.tokens[domain] -= 1.0
            return True
        return False
```

---

## Error Handling

| Scenario | Handling |
|----------|---------|
| HTTP 404 | Mark URL as `failed`, don't re-crawl |
| HTTP 429 (rate limited) | Exponential backoff, re-queue with delay |
| HTTP 5xx (server error) | Retry up to 3 times, then mark `failed` |
| DNS failure | Retry after 60s, mark domain temporarily unavailable |
| Timeout | Retry once, then skip |
| Robots.txt blocks | Skip URL entirely, mark `disallowed` |
| Redirect loop | Max 5 redirects, then discard |

---

## Key Interview Talking Points

```
1. Why Bloom Filter over HashSet?
   HashSet: 1B URLs × 100 bytes each = 100 GB RAM
   Bloom Filter: 1B URLs = 1.2 GB RAM (83x smaller)
   Tradeoff: 1% false positives → occasional re-crawl (acceptable)

2. Why Cassandra over MySQL?
   MySQL: single master, write bottleneck at billions of rows
   Cassandra: distributed, no master, linear write scaling
   Partition key = domain → all URLs for a domain on same node

3. Why Kafka over simple queue?
   Kafka: durable, replayable, partitioned by domain
   Simple queue: lost on crash, no domain isolation

4. Why async fetching?
   Fetching is I/O bound (waiting for network)
   Async: 1 thread, 10K concurrent requests
   Threads: 10K threads = ~80 GB RAM just for stack space

5. How to handle politeness at scale?
   Per-domain token bucket rate limiter
   robots.txt cached per domain (re-fetch weekly)
   Kafka partition per domain → sequential consumption = natural delay
```
