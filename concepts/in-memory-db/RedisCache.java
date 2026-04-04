import java.util.*;
import java.time.Instant;

/**
 * REDIS CACHE — Patterns in Java (without actual Redis dependency)
 *
 * Simulates the three most important cache patterns:
 *   1. Cache-Aside  — app checks cache, on miss reads DB + fills cache
 *   2. Write-Through — write to cache AND DB together
 *   3. TTL expiry    — entries auto-expire after a set time
 *
 * Also shows:
 *   - LRU eviction (least recently used)
 *   - Cache for a "find nearby drivers" use case
 *
 * In production: replace InMemoryCache with Jedis / Lettuce (Redis clients)
 *   Jedis:    jedis.set("key", "value"); jedis.get("key");
 *   Lettuce:  redisCommands.set("key", value); redisCommands.get("key");
 *
 * Run: javac RedisCache.java && java RedisCache
 */
class RedisCache {

    // ─── Cache Entry — stores value + expiry time ─────────────────────────────
    static class CacheEntry<V> {
        final V    value;
        final long expiresAt;   // epoch millis, -1 = no expiry

        CacheEntry(V value, long ttlSeconds) {
            this.value     = value;
            this.expiresAt = ttlSeconds < 0 ? -1 : Instant.now().toEpochMilli() + ttlSeconds * 1000;
        }

        boolean isExpired() {
            return expiresAt != -1 && Instant.now().toEpochMilli() > expiresAt;
        }
    }

    // ─── In-Memory Cache (simulates Redis) ───────────────────────────────────
    // Uses LinkedHashMap with access-order = true → LRU eviction
    static class InMemoryCache<K, V> {
        private final int maxSize;
        private final Map<K, CacheEntry<V>> store;

        InMemoryCache(int maxSize) {
            this.maxSize = maxSize;
            // accessOrder=true: get() moves entry to end → oldest = front = evicted first
            this.store = new LinkedHashMap<>(16, 0.75f, true) {
                @Override
                protected boolean removeEldestEntry(Map.Entry<K, CacheEntry<V>> eldest) {
                    return size() > maxSize; // LRU eviction when over capacity
                }
            };
        }

        void set(K key, V value, long ttlSeconds) {
            store.put(key, new CacheEntry<>(value, ttlSeconds));
        }

        Optional<V> get(K key) {
            CacheEntry<V> entry = store.get(key);
            if (entry == null)        return Optional.empty(); // miss
            if (entry.isExpired()) {
                store.remove(key);
                return Optional.empty(); // expired — treat as miss
            }
            return Optional.of(entry.value);
        }

        void delete(K key) { store.remove(key); }
        boolean exists(K key) { return get(key).isPresent(); }
        int size()  { return store.size(); }

        void printAll(String label) {
            System.out.println("  Cache [" + label + "] (" + store.size() + " entries):");
            store.forEach((k, v) -> {
                String exp = v.expiresAt == -1 ? "no-expiry" : "expires in ~" +
                    Math.max(0, (v.expiresAt - Instant.now().toEpochMilli()) / 1000) + "s";
                System.out.println("    " + k + " → " + v.value + "  [" + exp + "]");
            });
        }
    }

    // ─── Simulated DB ────────────────────────────────────────────────────────
    static class FakeDatabase {
        private final Map<String, String> data = new HashMap<>(Map.of(
            "user:1", "{name:Shubham, city:Mumbai}",
            "user:2", "{name:Alice,   city:Delhi}",
            "user:3", "{name:Bob,     city:Bangalore}"
        ));
        int readCount  = 0;
        int writeCount = 0;

        String read(String key) {
            readCount++;
            System.out.println("    [DB READ]  " + key);
            return data.get(key);
        }

        void write(String key, String value) {
            writeCount++;
            data.put(key, value);
            System.out.println("    [DB WRITE] " + key + " = " + value);
        }
    }

    // ─── Pattern 1: Cache-Aside ────────────────────────────────────────────────
    // App manages cache manually:
    //   Read:  check cache → hit: return | miss: read DB → store in cache → return
    //   Write: write to DB only → invalidate cache (next read will repopulate)
    static void cacheAsideDemo() {
        System.out.println("=== PATTERN 1: CACHE-ASIDE ===");

        InMemoryCache<String, String> cache = new InMemoryCache<>(100);
        FakeDatabase db = new FakeDatabase();

        // Read 1 — cache miss, goes to DB
        System.out.println("\nRead user:1 (first time — cache MISS):");
        String result = cache.get("user:1").orElseGet(() -> {
            String fromDb = db.read("user:1");
            cache.set("user:1", fromDb, 60); // cache for 60s
            return fromDb;
        });
        System.out.println("  Result: " + result);

        // Read 2 — cache hit, DB not touched
        System.out.println("\nRead user:1 (second time — cache HIT):");
        result = cache.get("user:1").orElseGet(() -> {
            String fromDb = db.read("user:1");
            cache.set("user:1", fromDb, 60);
            return fromDb;
        });
        System.out.println("  Result: " + result);

        // Write — update DB, invalidate cache
        System.out.println("\nUpdate user:1 city to Bangalore:");
        db.write("user:1", "{name:Shubham, city:Bangalore}");
        cache.delete("user:1"); // ← invalidate so next read gets fresh data
        System.out.println("  Cache invalidated");

        // Read 3 — cache miss again (was invalidated)
        System.out.println("\nRead user:1 (after update — cache MISS again):");
        result = cache.get("user:1").orElseGet(() -> {
            String fromDb = db.read("user:1");
            cache.set("user:1", fromDb, 60);
            return fromDb;
        });
        System.out.println("  Result: " + result);

        System.out.println("\nDB reads: " + db.readCount + " (saved 1 DB read with cache)");
    }

    // ─── Pattern 2: Write-Through ─────────────────────────────────────────────
    // Write to cache AND DB together — cache always consistent with DB
    // Trade-off: every write is slower (two writes), but reads are always fast
    static void writeThroughDemo() {
        System.out.println("\n=== PATTERN 2: WRITE-THROUGH ===");

        InMemoryCache<String, String> cache = new InMemoryCache<>(100);
        FakeDatabase db = new FakeDatabase();

        // Write-through helper
        // Both cache and DB updated atomically (in production: use a transaction)
        java.util.function.BiConsumer<String, String> writeThrough = (key, value) -> {
            db.write(key, value);          // write DB first
            cache.set(key, value, 300);    // then update cache
        };

        System.out.println("\nWrite user:1:");
        writeThrough.accept("user:1", "{name:Shubham, city:Pune}");

        System.out.println("\nRead user:1 (cache HIT — write-through already populated it):");
        cache.get("user:1").ifPresent(v -> System.out.println("  Result: " + v));

        System.out.println("\nDB reads: " + db.readCount + "  (zero — cache was warm from write)");
        System.out.println("DB writes: " + db.writeCount);
    }

    // ─── Pattern 3: TTL expiry ────────────────────────────────────────────────
    static void ttlDemo() throws InterruptedException {
        System.out.println("\n=== PATTERN 3: TTL EXPIRY ===");

        InMemoryCache<String, String> cache = new InMemoryCache<>(100);

        cache.set("session:abc", "user:42",  2); // expires in 2s
        cache.set("config:theme", "dark",   -1); // no expiry

        System.out.println("Just set session:abc (TTL=2s) and config:theme (no TTL)");
        cache.printAll("initial");

        System.out.println("\nWaiting 3 seconds...");
        Thread.sleep(3000);

        System.out.println("session:abc exists? " + cache.exists("session:abc")); // false
        System.out.println("config:theme exists? " + cache.exists("config:theme")); // true
        cache.printAll("after 3s");
    }

    // ─── Pattern 4: LRU eviction ──────────────────────────────────────────────
    static void lruDemo() {
        System.out.println("\n=== PATTERN 4: LRU EVICTION (maxSize=3) ===");

        InMemoryCache<String, String> cache = new InMemoryCache<>(3);

        cache.set("a", "alpha",   -1);
        cache.set("b", "beta",    -1);
        cache.set("c", "charlie", -1);
        System.out.println("After inserting a, b, c:"); cache.printAll("state");

        // Access 'a' — makes it recently used
        cache.get("a");
        System.out.println("\nAccessed 'a' (now most recently used)");

        // Insert 'd' — evicts LRU which is now 'b' (a was just accessed)
        cache.set("d", "delta", -1);
        System.out.println("After inserting 'd' (evicts LRU = 'b'):"); cache.printAll("state");

        System.out.println("'b' still in cache? " + cache.exists("b")); // false
        System.out.println("'a' still in cache? " + cache.exists("a")); // true
    }

    // ─── Pattern 5: Driver location cache (geo use case) ─────────────────────
    static void driverCacheDemo() {
        System.out.println("\n=== PATTERN 5: DRIVER LOCATION CACHE ===");
        System.out.println("(Uber-style: cache driver locations, expire if not updated)");

        InMemoryCache<String, String> driverCache = new InMemoryCache<>(10000);

        // Drivers update location every 4 seconds — TTL = 10s (miss 2 updates = gone)
        driverCache.set("driver:1", "19.0760,72.8777", 10);
        driverCache.set("driver:2", "18.9750,72.8296", 10);
        driverCache.set("driver:3", "19.1136,72.8659", 10);

        System.out.println("Active drivers:");
        for (String id : List.of("driver:1", "driver:2", "driver:3")) {
            driverCache.get(id).ifPresent(loc ->
                System.out.println("  " + id + " → " + loc)
            );
        }

        System.out.println("\nKey insight:");
        System.out.println("  Redis TTL = automatic cleanup of offline drivers");
        System.out.println("  No cron job needed — Redis expires keys automatically");
        System.out.println("  In Redis: SET driver:1 '19.07,72.88' EX 10");
    }

    public static void main(String[] args) throws InterruptedException {
        cacheAsideDemo();
        writeThroughDemo();
        ttlDemo();
        lruDemo();
        driverCacheDemo();

        System.out.println("""

        SUMMARY — CACHE PATTERNS:
          Cache-Aside   → app manages cache, DB is source of truth
                          write=invalidate cache, read=check cache first
          Write-Through → write updates BOTH cache+DB, reads always hit cache
                          slower writes, faster reads, strong consistency
          TTL           → auto-expire entries (sessions, driver locations)
          LRU eviction  → when cache full, remove least recently used

        REDIS COMMANDS equivalent:
          cache.set(k, v, ttl)  →  SET key value EX ttlSeconds
          cache.get(k)          →  GET key
          cache.delete(k)       →  DEL key
          cache.exists(k)       →  EXISTS key
          ttl remaining         →  TTL key
        """);
    }
}
