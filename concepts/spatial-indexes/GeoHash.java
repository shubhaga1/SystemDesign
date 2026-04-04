/**
 * GEOHASH — Encode lat/lng as a short string, nearby = similar prefix
 *
 * HOW IT WORKS:
 *   1. Divide the world in half repeatedly (binary subdivision).
 *   2. Interleave latitude bits and longitude bits.
 *   3. Encode those bits as a Base32 string.
 *
 *   Result: "te7uddsr" → Mumbai (8 chars = ~38m precision)
 *
 * KEY INSIGHT — Locality:
 *   Nearby locations share a prefix.
 *   "te7u" covers north Mumbai → all drivers in that area share this prefix.
 *   DB query: WHERE geohash LIKE 'te7u%' → finds all nearby points.
 *
 * PRECISION TABLE:
 *   1 char  ≈ 5,000 km × 5,000 km
 *   4 chars ≈ 40 km × 20 km
 *   6 chars ≈ 1.2 km × 0.6 km   ← city block
 *   8 chars ≈ 38m × 19m          ← building
 *   12 chars ≈ 3.7mm × 1.8mm     ← centimeter precision
 *
 * USED BY:
 *   Redis GEOADD/GEOSEARCH (internally geohash)
 *   Elasticsearch geo_point
 *   MongoDB 2dsphere index
 *   PostGIS
 *
 * Run: javac GeoHash.java && java GeoHash
 */
class GeoHash {

    private static final String BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz";

    // ─── Encode lat/lng → geohash string ─────────────────────────────────────
    static String encode(double lat, double lng, int precision) {
        double minLat = -90,  maxLat = 90;
        double minLng = -180, maxLng = 180;

        StringBuilder hash    = new StringBuilder();
        int           bits    = 0;
        int           bitsTotal = 0;
        int           hashVal = 0;
        boolean       isLng   = true; // alternate: lng bit, lat bit, lng bit...

        while (hash.length() < precision) {
            if (isLng) {
                // Longitude bisection
                double midLng = (minLng + maxLng) / 2;
                if (lng >= midLng) {
                    hashVal = (hashVal << 1) | 1;
                    minLng  = midLng;
                } else {
                    hashVal = (hashVal << 1);
                    maxLng  = midLng;
                }
            } else {
                // Latitude bisection
                double midLat = (minLat + maxLat) / 2;
                if (lat >= midLat) {
                    hashVal = (hashVal << 1) | 1;
                    minLat  = midLat;
                } else {
                    hashVal = (hashVal << 1);
                    maxLat  = midLat;
                }
            }

            isLng = !isLng;
            bitsTotal++;

            if (bitsTotal % 5 == 0) {           // 5 bits = one Base32 character
                hash.append(BASE32.charAt(hashVal));
                hashVal = 0;
            }
        }
        return hash.toString();
    }

    // ─── Decode geohash string → lat/lng bounding box ────────────────────────
    static double[] decode(String hash) {
        double minLat = -90,  maxLat = 90;
        double minLng = -180, maxLng = 180;
        boolean isLng = true;

        for (char c : hash.toCharArray()) {
            int val = BASE32.indexOf(c);
            for (int i = 4; i >= 0; i--) {          // 5 bits per char
                int bit = (val >> i) & 1;
                if (isLng) {
                    double mid = (minLng + maxLng) / 2;
                    if (bit == 1) minLng = mid; else maxLng = mid;
                } else {
                    double mid = (minLat + maxLat) / 2;
                    if (bit == 1) minLat = mid; else maxLat = mid;
                }
                isLng = !isLng;
            }
        }

        // Return center of bounding box
        return new double[]{
            (minLat + maxLat) / 2,
            (minLng + maxLng) / 2,
            minLat, maxLat, minLng, maxLng
        };
    }

    // ─── Get 8 neighbouring cells ─────────────────────────────────────────────
    // Every cell has 8 neighbours (N, NE, E, SE, S, SW, W, NW)
    // Used to handle boundary cases — a point near a cell edge may have
    // its nearest neighbour in an adjacent cell
    static String[] neighbours(String hash) {
        double[] decoded = decode(hash);
        double   lat     = decoded[0];
        double   lng     = decoded[1];

        // Approximate cell size at this precision level
        double latErr = (decoded[3] - decoded[2]) / 2;
        double lngErr = (decoded[5] - decoded[4]) / 2;
        int    prec   = hash.length();

        return new String[]{
            encode(lat + latErr * 2, lng,            prec), // N
            encode(lat + latErr * 2, lng + lngErr*2, prec), // NE
            encode(lat,              lng + lngErr*2, prec), // E
            encode(lat - latErr * 2, lng + lngErr*2, prec), // SE
            encode(lat - latErr * 2, lng,            prec), // S
            encode(lat - latErr * 2, lng - lngErr*2, prec), // SW
            encode(lat,              lng - lngErr*2, prec), // W
            encode(lat + latErr * 2, lng - lngErr*2, prec), // NW
        };
    }

    // ─── Shared prefix length (proximity measure) ─────────────────────────────
    static int sharedPrefix(String a, String b) {
        int i = 0;
        while (i < a.length() && i < b.length() && a.charAt(i) == b.charAt(i)) i++;
        return i;
    }

    // ─── Demo ─────────────────────────────────────────────────────────────────
    public static void main(String[] args) {

        // ── 1. Encode real locations ──────────────────────────────────────────
        System.out.println("=== 1. ENCODE LOCATIONS ===");

        double[][] locations = {
            {19.0760,  72.8777}, // Mumbai
            {19.0596,  72.8295}, // Bandra (close to Mumbai)
            {28.6139,  77.2090}, // Delhi
            {40.7128, -74.0060}, // New York
            {51.5074,  -0.1278}, // London
        };
        String[] names = {"Mumbai", "Bandra", "Delhi", "New York", "London"};

        System.out.printf("%-12s  %-8s  %-8s  %-10s  %-10s  %-10s%n",
                          "City", "Lat", "Lng", "Prec=4", "Prec=6", "Prec=8");
        System.out.println("-".repeat(70));
        for (int i = 0; i < locations.length; i++) {
            double lat = locations[i][0], lng = locations[i][1];
            System.out.printf("%-12s  %-8.4f  %-8.4f  %-10s  %-10s  %-10s%n",
                names[i], lat, lng,
                encode(lat, lng, 4),
                encode(lat, lng, 6),
                encode(lat, lng, 8)
            );
        }

        // ── 2. Locality — shared prefix ───────────────────────────────────────
        System.out.println("\n=== 2. LOCALITY — nearby = shared prefix ===");

        String mumbaiHash = encode(19.0760, 72.8777, 8);
        String bandraHash = encode(19.0596, 72.8295, 8);
        String delhiHash  = encode(28.6139, 77.2090, 8);
        String nycHash    = encode(40.7128, -74.006, 8);

        System.out.println("Mumbai  hash: " + mumbaiHash);
        System.out.println("Bandra  hash: " + bandraHash);
        System.out.println("Delhi   hash: " + delhiHash);
        System.out.println("NYC     hash: " + nycHash);
        System.out.println();
        System.out.println("Mumbai ↔ Bandra  shared prefix: " + sharedPrefix(mumbaiHash, bandraHash) + " chars  (close  ✅)");
        System.out.println("Mumbai ↔ Delhi   shared prefix: " + sharedPrefix(mumbaiHash, delhiHash)  + " chars  (far    ❌)");
        System.out.println("Mumbai ↔ NYC     shared prefix: " + sharedPrefix(mumbaiHash, nycHash)    + " chars  (very far ❌)");

        // ── 3. Decode back to lat/lng ─────────────────────────────────────────
        System.out.println("\n=== 3. DECODE — hash back to bounding box ===");

        double[] decoded = decode(mumbaiHash);
        System.out.printf("Hash: %s%n", mumbaiHash);
        System.out.printf("Center:   lat=%.6f  lng=%.6f%n", decoded[0], decoded[1]);
        System.out.printf("Bounds:   lat [%.6f, %.6f]  lng [%.6f, %.6f]%n",
                          decoded[2], decoded[3], decoded[4], decoded[5]);
        System.out.printf("Error:    ±%.2fm lat  ±%.2fm lng%n",
                          (decoded[3] - decoded[2]) / 2 * 111320,
                          (decoded[5] - decoded[4]) / 2 * 111320);

        // ── 4. Precision levels ───────────────────────────────────────────────
        System.out.println("\n=== 4. PRECISION LEVELS — Mumbai ===");
        System.out.printf("%-6s  %-12s  %s%n", "Length", "Hash", "Approx area");
        System.out.println("-".repeat(45));
        String[] areas = {"5000km²", "1250km²", "156km²", "~40×20km", "~5×5km",
                          "~1.2×0.6km", "~150×150m", "~38×19m"};
        for (int p = 1; p <= 8; p++) {
            System.out.printf("%-6d  %-12s  %s%n", p,
                encode(19.0760, 72.8777, p), areas[p - 1]);
        }

        // ── 5. Neighbours — handle boundary case ──────────────────────────────
        System.out.println("\n=== 5. NEIGHBOURS — cells adjacent to Mumbai ===");
        System.out.println("A user near a cell boundary may have drivers in the NEXT cell.");
        System.out.println("Solution: always search the cell + its 8 neighbours.\n");

        String cell = encode(19.0760, 72.8777, 6);
        System.out.println("Mumbai cell (prec=6): " + cell);
        String[] nbrs = neighbours(cell);
        String[] dirs = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
        for (int i = 0; i < 8; i++) {
            System.out.println("  " + dirs[i] + ": " + nbrs[i]);
        }

        // ── 6. DB range query ─────────────────────────────────────────────────
        System.out.println("\n=== 6. HOW DBs USE GEOHASH (range query) ===");
        System.out.println("""
          Store geohash in a column with a B-Tree index:

            CREATE TABLE drivers (
              id       VARCHAR,
              geohash  VARCHAR(8),   -- indexed
              lat      DOUBLE,
              lng      DOUBLE
            );
            CREATE INDEX idx_geo ON drivers(geohash);

          Search nearby (same cell prefix):
            -- All drivers in same geohash cell (precision 6 ≈ 1km):
            SELECT * FROM drivers WHERE geohash LIKE 'te7udq%';

            -- Also include 8 neighbours to avoid boundary misses:
            SELECT * FROM drivers WHERE geohash IN ('te7udq','te7udr','te7u7z',...);

            -- Post-filter by exact distance:
            SELECT *, haversine(lat, lng, 19.07, 72.88) AS dist
            FROM   drivers
            WHERE  geohash IN (...)
            ORDER  BY dist LIMIT 5;

          This is O(log n) index scan — not a full table scan.
        """);

        // ── 7. Geohash vs S2 vs QuadTree ──────────────────────────────────────
        System.out.println("=== 7. GEOHASH vs S2 vs QUADTREE ===");
        System.out.println("""
          Geohash:
            ✅ Simple string, easy to index in any DB
            ✅ Proximity = shared string prefix
            ❌ Rectangular cells → distortion near poles
            ❌ Boundary issue: nearby points can have very different hashes

          Google S2:
            ✅ Works on sphere — no pole distortion
            ✅ Uniform cell size globally
            ✅ Used by Google Maps, Uber
            ❌ 64-bit integer, harder to reason about

          QuadTree:
            ✅ In-memory, fast to build
            ✅ Good for dynamic data (drivers moving)
            ❌ Not stored in DB natively
            ❌ Rebuild on restart

          Redis GEOADD:
            ✅ Uses Geohash internally
            ✅ Distributed, persistent, production-ready
            ✅ GEOSEARCH in one command
            ❌ Limited polygon support
        """);
    }
}
