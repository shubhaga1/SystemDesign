/**
 * GOOGLE S2 — Spherical geometry spatial indexing
 *
 * IDEA:
 *   Map the SPHERE (Earth) onto a CUBE.
 *   Divide each cube face using a Hilbert curve into cells.
 *   Every cell gets a 64-bit integer ID.
 *   Nearby cells = similar IDs = efficient range queries.
 *
 * WHY S2 over QuadTree?
 *   QuadTree uses flat 2D (Mercator projection) → distortion near poles
 *   S2 works on the actual sphere → uniform cell sizes globally
 *
 * KEY CONCEPT — Hilbert Curve:
 *   A space-filling curve that preserves locality.
 *   Points close in 2D → close IDs on the curve → nearby range in DB.
 *
 * LEVELS: S2 has 31 levels of precision
 *   Level 0:  entire face of cube  (~85 million km²)
 *   Level 10: ~100km × 100km
 *   Level 14: ~6km × 6km
 *   Level 20: ~300m × 300m       ← common for POI search
 *   Level 30: ~1cm × 1cm
 *
 * USED BY:
 *   - Google Maps (exact algorithm)
 *   - Uber (driver indexing)
 *   - Foursquare
 *   - Pokemon Go
 *
 * This POC simulates S2 concepts WITHOUT the real library
 * (real: npm install s2geometry — C++ binding, hard to install)
 *
 * Run: node 02_google_s2.js
 */

// ─── S2 Cell ID simulation ────────────────────────────────────────────────────
// Real S2 uses face + Hilbert curve. We simulate with geohash-style bit interleaving.

class S2Cell {
    constructor(lat, lng, level = 14) {
        this.lat   = lat;
        this.lng   = lng;
        this.level = level;
        this.cellId = this._encode(lat, lng, level);
        this.token  = this._toToken(this.cellId);
    }

    // Simulate S2 cell ID: interleave lat/lng bits (simplified — real S2 uses Hilbert curve)
    _encode(lat, lng, level) {
        // Normalize to [0, 2^31)
        const latBits = Math.floor((lat + 90)  / 180 * (1 << 30));
        const lngBits = Math.floor((lng + 180) / 360 * (1 << 30));

        // Interleave bits (Morton code)
        let cell = BigInt(0);
        for (let i = 29; i >= 0; i--) {
            cell = (cell << BigInt(2)) |
                   (BigInt((latBits >> i) & 1) << BigInt(1)) |
                   BigInt((lngBits >> i) & 1);
        }
        // Apply level (truncate lower bits)
        const shift = BigInt(60 - level * 2);
        return (cell >> shift) << shift;
    }

    _toToken(cellId) {
        return cellId.toString(16).padStart(16, '0');
    }

    // Get the cell ID range that covers this cell at a given level
    coveringRange(level) {
        const shift = BigInt(60 - level * 2);
        const base  = (this.cellId >> shift) << shift;
        const size  = BigInt(1) << shift;
        return { min: base, max: base + size - BigInt(1) };
    }

    toString() {
        return `S2Cell(lat=${this.lat}, lng=${this.lng}, level=${this.level}, token=${this.token})`;
    }
}

// Check if two cells are neighbours (share a prefix at level-1)
function areNeighbours(cell1, cell2, level) {
    const shift = BigInt(60 - (level - 1) * 2);
    return (cell1.cellId >> shift) === (cell2.cellId >> shift);
}

// Get approximate cell size in km at a given level
function cellSizeKm(level) {
    // Earth circumference = 40,075 km, divided by 4 cube faces, then 4^level cells
    return 40075 / (4 * Math.pow(4, level) * 6) * 1000 / 1000;
}

// ─── Demo ─────────────────────────────────────────────────────────────────────
function main() {
    console.log('=== GOOGLE S2 — Spherical Spatial Indexing ===\n');

    // ─── 1. S2 Cell basics ───────────────────────────────────────────────────
    console.log('=== 1. S2 CELL — encode location ===');

    const mumbai   = new S2Cell(19.0760, 72.8777, 14);
    const bandra   = new S2Cell(19.0596, 72.8295, 14);
    const delhi    = new S2Cell(28.6139, 77.2090, 14);
    const nyc      = new S2Cell(40.7128, -74.0060, 14);

    console.log('Mumbai (level 14):', mumbai.token);
    console.log('Bandra (level 14):', bandra.token);
    console.log('Delhi  (level 14):', delhi.token);
    console.log('NYC    (level 14):', nyc.token);

    // ─── 2. Locality — nearby places = similar tokens ─────────────────────────
    console.log('\n=== 2. LOCALITY — nearby = similar cell IDs ===');

    // Compare first N hex chars — shared prefix = nearby
    const prefix = (token, chars) => token.slice(0, chars);

    console.log(`Mumbai prefix(6): ${prefix(mumbai.token, 6)}`);
    console.log(`Bandra prefix(6): ${prefix(bandra.token, 6)}`);
    console.log(`Delhi  prefix(6): ${prefix(delhi.token, 6)}`);
    console.log(`NYC    prefix(6): ${prefix(nyc.token, 6)}`);
    console.log('\nMumbai and Bandra share more prefix → closer together ✅');

    // ─── 3. Levels — precision ────────────────────────────────────────────────
    console.log('\n=== 3. LEVELS — more level = smaller cell ===');

    for (const level of [5, 10, 14, 18, 22]) {
        const c = new S2Cell(19.0760, 72.8777, level);
        console.log(`  Level ${String(level).padStart(2)}: token=${c.token}  approx size ≈ ${cellSizeKm(level).toFixed(1)} km`);
    }

    // ─── 4. Range query — how DBs use S2 ─────────────────────────────────────
    console.log('\n=== 4. RANGE QUERY — how S2 is used in a DB ===');
    console.log(`
  1. On write: store (cell_id, lat, lng, driver_id) in DB
               index on cell_id

  2. On query: compute cell covering for search radius
               SELECT * WHERE cell_id BETWEEN min AND max
               (single range scan — no expensive distance calc on all rows)

  3. Post-filter: calculate exact distance for remaining rows
  `);

    const userCell = new S2Cell(19.0700, 72.8400, 14);
    const range    = userCell.coveringRange(13);  // level 13 = ~12km cell
    console.log(`User cell (level 14): ${userCell.token}`);
    console.log(`Level 13 range: ${range.min.toString(16)} → ${range.max.toString(16)}`);
    console.log(`SQL: WHERE cell_id >= ${range.min} AND cell_id <= ${range.max}`);

    // ─── 5. S2 vs Geohash vs QuadTree ────────────────────────────────────────
    console.log('\n=== 5. S2 vs GEOHASH vs QUADTREE ===');
    console.log(`
  ┌─────────────┬──────────────────┬────────────────┬──────────────────┐
  │             │ Geohash (Redis)  │ QuadTree       │ Google S2        │
  ├─────────────┼──────────────────┼────────────────┼──────────────────┤
  │ Projection  │ Flat (Mercator)  │ Flat (2D box)  │ Sphere (no dist) │
  │ Cell shape  │ Rectangle        │ Square         │ Curved square    │
  │ Distortion  │ Near poles       │ Near poles     │ None ✅           │
  │ Cell size   │ Varies by lat    │ Fixed          │ Uniform globally │
  │ Use in DB   │ Sorted Set score │ Tree structure │ Integer range    │
  │ Prefix query│ String prefix    │ Node traversal │ Integer range    │
  │ Used by     │ Redis            │ Games, Maps    │ Google, Uber     │
  └─────────────┴──────────────────┴────────────────┴──────────────────┘
  `);

    // ─── 6. Hilbert curve — why IDs preserve locality ─────────────────────────
    console.log('=== 6. HILBERT CURVE — why nearby points = nearby IDs ===');
    console.log(`
  Normal grid numbering:              Hilbert curve numbering:
  ┌───┬───┬───┬───┐                  ┌───┬───┬───┬───┐
  │ 0 │ 1 │ 2 │ 3 │                  │ 0 │ 1 │14 │15 │
  ├───┼───┼───┼───┤                  ├───┼───┼───┼───┤
  │ 4 │ 5 │ 6 │ 7 │                  │ 3 │ 2 │13 │12 │
  ├───┼───┼───┼───┤                  ├───┼───┼───┼───┤
  │ 8 │ 9 │10 │11 │                  │ 4 │ 7 │ 8 │11 │
  ├───┼───┼───┼───┤                  ├───┼───┼───┼───┤
  │12 │13 │14 │15 │                  │ 5 │ 6 │ 9 │10 │
  └───┴───┴───┴───┘                  └───┴───┴───┴───┘

  Normal: cells 3 and 4 are adjacent but 3 apart in ID (bad for range queries)
  Hilbert: cells 3 and 4 → nearby cells have nearby IDs → DB range scan works!
  `);

    // ─── 7. Practical: which level to use? ───────────────────────────────────
    console.log('=== 7. WHICH LEVEL TO USE? ===');
    console.log(`
  Search radius    →  S2 level   →  Cell size
  1km              →  Level 15   →  ~600m × 600m
  5km              →  Level 13   →  ~2.5km × 2.5km
  50km             →  Level 10   →  ~20km × 20km

  Rule: cell size ≈ radius / 2  (so 4–9 cells cover your search area)

  Uber uses level 12 for city-level aggregation
  Uber uses level 15 for driver location lookup (~1km cells)
  `);
}

main();
