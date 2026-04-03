/**
 * R-TREE — Spatial index for rectangles and polygons
 *
 * IDEA:
 *   Group nearby objects into Minimum Bounding Rectangles (MBR).
 *   Tree of MBRs — search only boxes that overlap your query box.
 *
 * WHY R-Tree vs QuadTree?
 *   QuadTree: divides SPACE into fixed quadrants (even if empty)
 *   R-Tree:   groups DATA into tight bounding boxes (no wasted space)
 *
 * USED BY:
 *   - PostgreSQL PostGIS (geospatial queries)
 *   - SQLite (R*Tree extension)
 *   - Uber's H3 (underlying index)
 *   - Computer graphics (bounding box collision)
 *   - Spatial databases for polygons (delivery zones, geofences)
 *
 * PERFECT FOR:
 *   - Rectangles, polygons (not just points)
 *   - Overlapping region queries ("which zones does this point fall in?")
 *   - PostGIS: delivery zone lookup, geofencing
 *
 * Run: node 03_rtree.js
 */

// ─── Bounding Box ─────────────────────────────────────────────────────────────
class BBox {
    constructor(minX, minY, maxX, maxY) {
        this.minX = minX;
        this.minY = minY;
        this.maxX = maxX;
        this.maxY = maxY;
    }

    // Area of this bounding box
    area() {
        return (this.maxX - this.minX) * (this.maxY - this.minY);
    }

    // Does this box contain a point?
    containsPoint(x, y) {
        return x >= this.minX && x <= this.maxX &&
               y >= this.minY && y <= this.maxY;
    }

    // Does this box intersect another box?
    intersects(other) {
        return !(other.minX > this.maxX || other.maxX < this.minX ||
                 other.minY > this.maxY || other.maxY < this.minY);
    }

    // Expand to include another box (used when inserting)
    expand(other) {
        return new BBox(
            Math.min(this.minX, other.minX),
            Math.min(this.minY, other.minY),
            Math.max(this.maxX, other.maxX),
            Math.max(this.maxY, other.maxY)
        );
    }

    // How much would area increase if we added another box?
    enlargement(other) {
        return this.expand(other).area() - this.area();
    }

    toString() {
        return `[${this.minX},${this.minY} → ${this.maxX},${this.maxY}]`;
    }
}

// ─── R-Tree Node ──────────────────────────────────────────────────────────────
class RTreeNode {
    constructor(isLeaf = true) {
        this.isLeaf   = isLeaf;
        this.bbox     = null;          // bounding box of all children
        this.children = [];            // RTreeNode[] or Entry[]
    }

    updateBBox() {
        if (this.children.length === 0) return;
        this.bbox = this.children.reduce(
            (acc, child) => acc ? acc.expand(child.bbox) : child.bbox,
            null
        );
    }
}

// ─── R-Tree ───────────────────────────────────────────────────────────────────
class RTree {
    constructor(maxEntries = 4) {
        this.maxEntries = maxEntries;   // max children per node before split
        this.minEntries = Math.floor(maxEntries / 2);
        this.root       = new RTreeNode(true);
    }

    // Insert a spatial object with a bounding box
    insert(bbox, data) {
        const entry = { bbox, data };
        this._insert(entry, this.root, 0);
    }

    _insert(entry, node, depth) {
        if (node.isLeaf) {
            node.children.push(entry);
        } else {
            // Choose child whose bbox needs least enlargement
            const best = this._chooseBestChild(node, entry.bbox);
            this._insert(entry, best, depth + 1);
            best.updateBBox();
        }

        // Split if over capacity
        if (node.children.length > this.maxEntries) {
            this._split(node);
        }

        node.updateBBox();
    }

    _chooseBestChild(node, bbox) {
        let bestChild  = null;
        let bestEnlarge = Infinity;
        let bestArea    = Infinity;

        for (const child of node.children) {
            const enlarge = child.bbox.enlargement(bbox);
            if (enlarge < bestEnlarge ||
               (enlarge === bestEnlarge && child.bbox.area() < bestArea)) {
                bestChild   = child;
                bestEnlarge = enlarge;
                bestArea    = child.bbox.area();
            }
        }
        return bestChild;
    }

    // Simple linear split — pick two seeds, partition rest
    _split(node) {
        const entries = node.children;

        // Pick seed 1: leftmost minX, seed 2: rightmost maxX
        let seed1 = entries.reduce((a, b) => a.bbox.minX < b.bbox.minX ? a : b);
        let seed2 = entries.reduce((a, b) => a.bbox.maxX > b.bbox.maxX ? a : b);

        if (seed1 === seed2) seed2 = entries.find(e => e !== seed1);

        const group1 = [seed1];
        const group2 = [seed2];
        const bbox1  = seed1.bbox;
        const bbox2  = seed2.bbox;

        for (const e of entries) {
            if (e === seed1 || e === seed2) continue;
            const d1 = bbox1.enlargement(e.bbox);
            const d2 = bbox2.enlargement(e.bbox);
            if (d1 <= d2) group1.push(e);
            else          group2.push(e);
        }

        // Keep group1 in this node, promote group2 as sibling
        node.children = group1;
        node.updateBBox();

        const sibling = new RTreeNode(node.isLeaf);
        sibling.children = group2;
        sibling.updateBBox();

        // If root split, create new root
        if (node === this.root) {
            const newRoot = new RTreeNode(false);
            newRoot.children = [node, sibling];
            newRoot.updateBBox();
            this.root = newRoot;
        } else {
            // Parent will handle the sibling (simplified — production R-Trees handle this properly)
            this.root.children.push(sibling);
            this.root.updateBBox();
        }
    }

    // Find all entries whose bbox intersects the query bbox
    search(queryBBox, node = this.root, result = []) {
        if (!node.bbox || !node.bbox.intersects(queryBBox)) return result;

        if (node.isLeaf) {
            for (const entry of node.children) {
                if (entry.bbox.intersects(queryBBox)) {
                    result.push(entry);
                }
            }
        } else {
            for (const child of node.children) {
                this.search(queryBBox, child, result);
            }
        }
        return result;
    }

    // Point-in-polygon: which zones contain this point?
    pointSearch(x, y) {
        const pointBox = new BBox(x, y, x, y);
        return this.search(pointBox).filter(e =>
            e.bbox.containsPoint(x, y)
        );
    }

    stats(node = this.root, depth = 0) {
        const indent = '  '.repeat(depth);
        console.log(`${indent}Node(leaf=${node.isLeaf}, children=${node.children.length}, bbox=${node.bbox})`);
        if (!node.isLeaf) {
            for (const child of node.children) this.stats(child, depth + 1);
        }
    }
}

// ─── Demo ─────────────────────────────────────────────────────────────────────
function main() {
    console.log('=== R-TREE — Rectangle/Region Spatial Index ===\n');

    const rt = new RTree(4);

    // ─── 1. Insert delivery zones (polygons simplified as bounding boxes) ─────
    console.log('=== 1. INSERT — delivery zones as bounding boxes ===');

    const zones = [
        { name: 'Bandra Zone',      bbox: new BBox(72.82, 19.04, 72.88, 19.07) },
        { name: 'Andheri Zone',     bbox: new BBox(72.83, 19.09, 72.89, 19.14) },
        { name: 'Dadar Zone',       bbox: new BBox(72.81, 18.97, 72.85, 19.02) },
        { name: 'Worli Zone',       bbox: new BBox(72.80, 18.97, 72.84, 19.00) },
        { name: 'Fort Zone',        bbox: new BBox(72.82, 18.92, 72.85, 18.96) },
        { name: 'Powai Zone',       bbox: new BBox(72.89, 19.10, 72.93, 19.14) },
        { name: 'Santacruz Zone',   bbox: new BBox(72.83, 19.06, 72.87, 19.09) },
        { name: 'Goregaon Zone',    bbox: new BBox(72.84, 19.14, 72.88, 19.18) },
    ];

    for (const z of zones) {
        rt.insert(z.bbox, z.name);
        console.log(`  + ${z.name}: ${z.bbox}`);
    }

    // ─── 2. Search — which zones overlap a search area ────────────────────────
    console.log('\n=== 2. RANGE SEARCH — zones in search area ===');

    const searchArea = new BBox(72.82, 19.04, 72.87, 19.09);
    console.log(`Search area: ${searchArea}`);

    const found = rt.search(searchArea);
    console.log(`Overlapping zones (${found.length}):`);
    found.forEach(e => console.log(`  → ${e.data}`));

    // ─── 3. Point query — which zone does this point fall in? ─────────────────
    console.log('\n=== 3. POINT QUERY — which zone contains this point? ===');

    const points = [
        { x: 72.855, y: 19.055, label: 'User A (Bandra area)' },
        { x: 72.850, y: 18.985, label: 'User B (Dadar area)'  },
        { x: 72.910, y: 19.120, label: 'User C (Powai area)'  },
        { x: 72.900, y: 18.850, label: 'User D (no zone)'     },
    ];

    for (const p of points) {
        const zones = rt.pointSearch(p.x, p.y);
        const zoneNames = zones.map(e => e.data).join(', ') || 'None';
        console.log(`  ${p.label} → ${zoneNames}`);
    }

    // ─── 4. Geofencing use case ────────────────────────────────────────────────
    console.log('\n=== 4. GEOFENCING — "alert when driver enters zone" ===');
    console.log(`
  Pattern:
    1. Store geofence polygons in R-Tree on startup
    2. On each driver location update:
       zones = rtree.pointSearch(driver.lat, driver.lng)
       if zones.length > 0:
           trigger zone-entry event(driver, zones)

  This is O(log n) not O(n) — critical at Uber scale:
    1M drivers × 100K zones = R-Tree handles in microseconds
    Naive: 1M × 100K = 100 billion checks per tick ❌
  `);

    // ─── 5. R-Tree vs QuadTree vs S2 ──────────────────────────────────────────
    console.log('=== 5. WHEN TO USE WHICH ===');
    console.log(`
  ┌──────────────┬──────────────────────┬────────────────────────────────┐
  │              │ Best for             │ Not good for                   │
  ├──────────────┼──────────────────────┼────────────────────────────────┤
  │ QuadTree     │ Point data, in-memory│ Rectangles, clustered data     │
  │              │ Game collision       │ Polar distortion               │
  ├──────────────┼──────────────────────┼────────────────────────────────┤
  │ Google S2    │ Spherical accuracy   │ Simple use cases               │
  │              │ Global apps, Uber    │ Polygons (needs extra work)    │
  ├──────────────┼──────────────────────┼────────────────────────────────┤
  │ R-Tree       │ Rectangles, polygons │ Point queries (R-Tree is bulky)│
  │              │ Geofencing, PostGIS  │ In-memory (better use QT/S2)  │
  ├──────────────┼──────────────────────┼────────────────────────────────┤
  │ Redis GEO    │ Fast, distributed    │ Polygons                       │
  │              │ Nearest N drivers    │ Complex region queries         │
  └──────────────┴──────────────────────┴────────────────────────────────┘

  Real systems combine them:
    Uber: S2 for driver indexing + R-Tree for surge zones
    Google Maps: S2 for cells + R-Tree for road segments
    PostGIS: R-Tree index over polygon geometries
  `);
}

main();
