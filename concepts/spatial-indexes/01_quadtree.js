/**
 * QUADTREE — Spatial index for 2D point data
 *
 * IDEA:
 *   Divide a 2D space into 4 quadrants recursively.
 *   Each node holds up to MAX_POINTS before splitting.
 *   Finding nearby points = only search relevant quadrants.
 *
 * WHY:
 *   Naive approach: check ALL points → O(n) per query
 *   QuadTree:       skip quadrants far away → O(log n) avg
 *
 * USED BY:
 *   - Twitter to index tweet locations
 *   - Game engines for collision detection
 *   - Maps for POI (point of interest) search
 *
 * vs Redis GEO:
 *   Redis GEO  = production ready, distributed, persistent
 *   QuadTree   = understand the concept, implement in-process
 *
 * Run: node 01_quadtree.js
 */

// ─── Rectangle bounds ─────────────────────────────────────────────────────────
class Rectangle {
    constructor(x, y, width, height) {
        this.x      = x;       // center x
        this.y      = y;       // center y
        this.width  = width;   // half-width
        this.height = height;  // half-height
    }

    // Does this rectangle contain this point?
    contains(point) {
        return point.x >= this.x - this.width  &&
               point.x <= this.x + this.width  &&
               point.y >= this.y - this.height &&
               point.y <= this.y + this.height;
    }

    // Does this rectangle intersect (overlap) another rectangle?
    intersects(other) {
        return !(other.x - other.width  >  this.x + this.width  ||
                 other.x + other.width  <  this.x - this.width  ||
                 other.y - other.height >  this.y + this.height ||
                 other.y + other.height <  this.y - this.height);
    }
}

// ─── QuadTree ─────────────────────────────────────────────────────────────────
class QuadTree {
    constructor(boundary, maxPoints = 4) {
        this.boundary  = boundary;   // Rectangle defining this node's area
        this.maxPoints = maxPoints;  // max points before splitting
        this.points    = [];         // points stored here (leaf node)
        this.divided   = false;      // has this node been split?

        // Four children (null until split needed)
        this.northeast = null;
        this.northwest = null;
        this.southeast = null;
        this.southwest = null;
    }

    // Split this node into 4 children
    subdivide() {
        const { x, y, width, height } = this.boundary;
        const hw = width  / 2;   // half of half = quarter
        const hh = height / 2;

        this.northeast = new QuadTree(new Rectangle(x + hw, y - hh, hw, hh), this.maxPoints);
        this.northwest = new QuadTree(new Rectangle(x - hw, y - hh, hw, hh), this.maxPoints);
        this.southeast = new QuadTree(new Rectangle(x + hw, y + hh, hw, hh), this.maxPoints);
        this.southwest = new QuadTree(new Rectangle(x - hw, y + hh, hw, hh), this.maxPoints);

        this.divided = true;

        // Re-insert existing points into children
        for (const p of this.points) {
            this._insertIntoChildren(p);
        }
        this.points = []; // parent no longer holds points after split
    }

    _insertIntoChildren(point) {
        this.northeast.insert(point) ||
        this.northwest.insert(point) ||
        this.southeast.insert(point) ||
        this.southwest.insert(point);
    }

    // Insert a point — returns true if inserted
    insert(point) {
        // Point outside this node's boundary
        if (!this.boundary.contains(point)) return false;

        if (!this.divided) {
            if (this.points.length < this.maxPoints) {
                this.points.push(point);
                return true;
            }
            // At capacity — split into 4
            this.subdivide();
        }

        // Try inserting into children
        return this._insertIntoChildren(point);
    }

    // Find all points within a given range (Rectangle)
    query(range, found = []) {
        // Skip this node if range doesn't intersect it
        if (!this.boundary.intersects(range)) return found;

        // Check leaf points
        for (const p of this.points) {
            if (range.contains(p)) found.push(p);
        }

        // Recurse into children
        if (this.divided) {
            this.northeast.query(range, found);
            this.northwest.query(range, found);
            this.southeast.query(range, found);
            this.southwest.query(range, found);
        }

        return found;
    }

    // Count total nodes (for visualisation)
    countNodes() {
        if (!this.divided) return 1;
        return 1 +
            this.northeast.countNodes() +
            this.northwest.countNodes() +
            this.southeast.countNodes() +
            this.southwest.countNodes();
    }

    // Count depth
    depth() {
        if (!this.divided) return 0;
        return 1 + Math.max(
            this.northeast.depth(),
            this.northwest.depth(),
            this.southeast.depth(),
            this.southwest.depth()
        );
    }
}

// ─── Distance helper ──────────────────────────────────────────────────────────
function dist(a, b) {
    return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}

// Find nearest N points to a location using QuadTree
function findNearest(qt, point, n, searchRadius) {
    const range  = new Rectangle(point.x, point.y, searchRadius, searchRadius);
    const nearby = qt.query(range);
    return nearby
        .map(p => ({ ...p, distance: dist(p, point) }))
        .sort((a, b) => a.distance - b.distance)
        .slice(0, n);
}

// ─── Demo ─────────────────────────────────────────────────────────────────────
function main() {
    console.log('=== QUADTREE — 2D Spatial Index ===\n');

    // World bounds: x [-180,180] lng, y [-90,90] lat
    const world = new Rectangle(0, 0, 180, 90);
    const qt    = new QuadTree(world, 4); // split after 4 points

    // Insert Mumbai area drivers
    const drivers = [
        { x:  72.88, y: -19.08, id: 'D1', name: 'Rahul  (Bandra)'  },
        { x:  72.83, y: -18.98, id: 'D2', name: 'Amit   (Dadar)'   },
        { x:  72.87, y: -19.11, id: 'D3', name: 'Vijay  (Andheri)' },
        { x:  72.83, y: -18.99, id: 'D4', name: 'Suresh (Worli)'   },
        { x:  72.91, y: -19.12, id: 'D5', name: 'Kiran  (Powai)'   },
        { x:  72.83, y: -18.93, id: 'D6', name: 'Dev    (Parel)'   },
        { x:  72.82, y: -19.04, id: 'D7', name: 'Raj    (Khar)'    },
        { x:  72.85, y: -19.15, id: 'D8', name: 'Sam    (Goregaon)'},
    ];

    console.log('Inserting drivers...');
    for (const d of drivers) {
        qt.insert(d);
        console.log(`  + ${d.name}`);
    }

    console.log(`\nQuadTree stats:`);
    console.log(`  Nodes:  ${qt.countNodes()}`);
    console.log(`  Depth:  ${qt.depth()}`);

    // Query: find drivers near user (Fort area)
    const user = { x: 72.84, y: -18.97 };
    console.log(`\n=== QUERY — find drivers near user (${user.x}, ${user.y}) ===`);

    // Search radius 0.1 degrees ≈ ~11km
    const nearest = findNearest(qt, user, 3, 0.1);
    console.log(`Top 3 nearest drivers:`);
    nearest.forEach((d, i) => {
        console.log(`  ${i+1}. ${d.name.padEnd(25)} distance=${d.distance.toFixed(4)} deg`);
    });

    // Range query — box around user
    const searchBox = new Rectangle(user.x, user.y, 0.05, 0.05);
    const inBox     = qt.query(searchBox);
    console.log(`\nDrivers in tight box (0.05deg radius): ${inBox.length}`);
    inBox.forEach(d => console.log(`  → ${d.name}`));

    // ─── Naive vs QuadTree comparison ────────────────────────────────────────
    console.log('\n=== NAIVE vs QUADTREE ===');

    const N = 10000;
    const bigPoints = Array.from({ length: N }, (_, i) => ({
        x: (Math.random() * 360) - 180,
        y: (Math.random() * 180) - 90,
        id: i
    }));

    // Naive: scan all points
    const t1 = Date.now();
    const target = { x: 72.84, y: -18.97 };
    const naiveResult = bigPoints
        .filter(p => Math.abs(p.x - target.x) < 5 && Math.abs(p.y - target.y) < 5);
    console.log(`Naive scan    (${N} points): ${Date.now() - t1}ms → found ${naiveResult.length}`);

    // QuadTree
    const worldBig = new Rectangle(0, 0, 180, 90);
    const bigQt    = new QuadTree(worldBig, 8);
    const t2 = Date.now();
    for (const p of bigPoints) bigQt.insert(p);
    const buildTime = Date.now() - t2;

    const t3 = Date.now();
    const qtResult = bigQt.query(new Rectangle(target.x, target.y, 5, 5));
    const queryTime = Date.now() - t3;

    console.log(`QuadTree build  (${N} points): ${buildTime}ms`);
    console.log(`QuadTree query  (${N} points): ${queryTime}ms → found ${qtResult.length}`);

    console.log(`
KEY POINTS:
  QuadTree splits space into 4 when a cell gets too full
  Query skips entire quadrants that can't contain the answer
  Good for: uniform 2D data, in-memory, game engines, maps
  Bad for:  clustered data (one quadrant fills up), 3D data
  Time:     O(log n) average query, O(n log n) build
    `);
}

main();
