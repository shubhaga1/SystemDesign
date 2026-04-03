# In-Memory Databases — Redis

## What is an in-memory database?

Data is stored in RAM instead of disk.

```
Disk read:   10 ms
RAM read:    100 ns   ← 100,000x faster
```

You pay more (RAM is expensive), but reads are near-instant.

---

## Redis vs Memcached

| | Redis | Memcached |
| --- | --- | --- |
| Data types | String, List, Set, Hash, SortedSet, Geo, Stream | String only |
| Persistence | Yes (RDB snapshots + AOF logs) | No — restart = all gone |
| Pub/Sub | Yes | No |
| Geolocation | Yes (GEOADD, GEORADIUS) | No |
| Clustering | Yes | Yes |
| Lua scripting | Yes | No |
| **Use when** | Rich data types, persistence needed | Simple key-value cache only |

**Rule:** Default to Redis unless you have a specific reason for Memcached.

---

## Redis data types

| Type | Commands | Real use |
| --- | --- | --- |
| String | GET, SET, INCR | Cache any value, counters |
| List | LPUSH, RPOP, LRANGE | Message queues, activity feeds |
| Set | SADD, SMEMBERS, SINTER | Unique visitors, tags |
| Hash | HSET, HGET, HGETALL | User profile, session data |
| Sorted Set | ZADD, ZRANGE, ZRANK | Leaderboards, priority queues |
| Geo | GEOADD, GEORADIUS, GEODIST | Nearby search (Uber, food delivery) |
| Stream | XADD, XREAD | Event log, real-time analytics |

---

## Files in this folder

| File | What it shows |
| --- | --- |
| `01_redis_basics.js` | Core commands — String, Hash, List, Set, SortedSet |
| `02_geolocation.js` | Geo commands — add locations, find nearby, get distance |
| `docker-compose.yml` | Start Redis locally with one command |
| `package.json` | Node dependencies |

---

## Quick start

```bash
# 1. Start Redis
docker-compose up -d

# 2. Run basics
node 01_redis_basics.js

# 3. Run geolocation POC
node 02_geolocation.js

# 4. Connect to Redis CLI manually
docker exec -it redis-local redis-cli
```

---

## When to use Redis for caching

```
User hits API
→ Check Redis first (cache hit = return in <1ms)
→ Cache miss → query DB → store result in Redis with TTL
→ Next request = cache hit

TTL (Time To Live) = expiry time
  Set short TTL (60s) for real-time data (stock prices)
  Set long TTL (1h) for stable data (user profile)
```

---

## Geolocation in Redis — how it works

Redis stores geo coordinates using **Geohash** — a 52-bit integer that encodes latitude/longitude.

```
GEOADD drivers 72.8777 19.0760 "driver:1"
              ↑lng    ↑lat    ↑member name

Internally stored as a Sorted Set with score = geohash integer
This lets Redis do range queries (nearby search) in O(N+log M)
```

Real use cases:
- **Uber/Lyft** — find drivers within 2km of rider
- **Swiggy/Zomato** — find restaurants within delivery radius
- **Bumble** — find users near you
- **Google Maps** — POI search (ATMs, restaurants nearby)
