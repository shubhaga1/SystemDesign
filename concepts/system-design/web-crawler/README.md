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

| Parameter | Value | Notes |
|-----------|-------|-------|
| Total pages | 1 billion | Target crawl size |
| Avg page size | 100 KB | Per page estimate |
| Total data/cycle | ~10 PB | Full crawl every 7 days |
| Daily data volume | ~1.3 PB | 10 PB ÷ 7 |
| Bandwidth needed | ~3 GB/sec | Sustained throughput |

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
README.md        ← this file (requirements, capacity, workflow, HLD)
hld.md           ← High Level Design (component diagram, tech choices)
lld.md           ← Low Level Design (DB schema, class design, APIs)
code/
  crawler.py     ← runnable POC (Scheduler, PriorityQueue, BloomFilter, Fetcher)
```
