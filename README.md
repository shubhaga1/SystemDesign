# System Design — Learning Repository

Structured notes, concepts, and runnable POCs for mastering system design.

---

## Learning Path

| # | Folder | What you learn |
| --- | --- | --- |
| 1 | `concepts/` | Core building blocks — cache, DB, queues, CDN |
| 2 | `HLD/` | High-level design — architecture diagrams, trade-offs |
| 3 | `LLD/` | Low-level design — class diagrams, OOP, design patterns |
| 4 | `API/` | REST, GraphQL, gRPC — design and versioning |
| 5 | `project/` | End-to-end system design walkthroughs |

---

## concepts/

Deep dives into individual system building blocks.  
Each folder has a README explaining the concept + runnable code POCs.

| Folder | Topic |
| --- | --- |
| `in-memory-db/` | Redis — caching, pub/sub, geolocation, leaderboards |

---

## How to run POCs

Most POCs are Node.js — no framework needed.

```bash
# Start dependencies (Redis etc.)
docker-compose up -d

# Run any POC
node 02_geolocation.js
```

---

## Key System Design Concepts (quick reference)

### Scalability
- **Vertical scaling** — bigger machine (CPU, RAM)
- **Horizontal scaling** — more machines (preferred for web)
- **Load balancer** — distributes traffic across servers

### Storage
| Type | Examples | Use when |
| --- | --- | --- |
| Relational DB | PostgreSQL, MySQL | Structured data, ACID transactions |
| NoSQL | MongoDB, Cassandra | Flexible schema, massive scale |
| In-memory | Redis, Memcached | Sub-millisecond reads, caching |
| Object store | S3 | Files, images, backups |
| Search | Elasticsearch | Full-text search, log analysis |

### CAP Theorem
Every distributed system can only guarantee 2 of 3:
- **C**onsistency — every read gets the latest write
- **A**vailability — every request gets a response
- **P**artition tolerance — system works despite network splits

Most systems choose **AP** (available + partition tolerant) or **CP** (consistent + partition tolerant).

### Caching patterns
| Pattern | How | Use case |
| --- | --- | --- |
| Cache-aside | App checks cache, on miss reads DB + fills cache | Most common |
| Write-through | Write to cache AND DB together | Strong consistency |
| Write-behind | Write to cache, async flush to DB | High write throughput |
| Read-through | Cache sits in front of DB, auto-populates | Transparent to app |

### Numbers every engineer should know
```
L1 cache read:          0.5 ns
Main memory read:       100 ns
SSD read:               100 µs
Network round-trip:     1–10 ms
HDD read:               10 ms
```

---

*Work in progress — adding concepts and POCs regularly.*
