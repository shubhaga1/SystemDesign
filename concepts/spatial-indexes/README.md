# Spatial Indexes — QuadTree, Google S2, R-Tree

How location-based systems find "nearby" things at scale.

## The core problem

```
You have 10 million drivers on Uber.
A rider requests a cab.
How do you find the 5 nearest drivers in <100ms?

Naive: check all 10M drivers → too slow
Solution: spatial index → skip most of the data
```

---

## Three approaches

| | QuadTree | Google S2 | R-Tree |
| --- | --- | --- | --- |
| **Splits** | Space into 4 quadrants | Sphere into cells (Hilbert curve) | Data into bounding boxes |
| **Shape** | Square cells | Curved cells on sphere | Tight rectangles around data |
| **Best for** | Point data, games | Global apps, sphere accuracy | Polygons, geofences |
| **Used by** | Game engines, Twitter | Google Maps, Uber, Pokémon Go | PostGIS, SQLite |
| **Distortion** | Near poles | None ✅ | None ✅ |

---

## Files

| File | What it shows |
| --- | --- |
| `01_quadtree.js` | Split 2D space into 4, query nearby points, naive vs QuadTree perf |
| `02_google_s2.js` | S2 cell IDs, Hilbert curve locality, levels, DB range queries |
| `03_rtree.js` | MBR grouping, range search, point-in-polygon, geofencing |

```bash
node 01_quadtree.js
node 02_google_s2.js
node 03_rtree.js
```

---

## How each does "find nearby drivers"

**QuadTree:**
```
Query box → traverse tree → skip far quadrants → check leaf points
```

**S2:**
```
lat/lng → S2 cell ID (integer) → DB range scan on cell_id column
WHERE cell_id BETWEEN X AND Y
```

**R-Tree:**
```
Query box → check which MBRs intersect → recurse into matching subtrees
```

---

## Real system design: Uber

```
Driver location update (every 4s):
  → Compute S2 cell ID at level 15 (~600m cell)
  → Store in Redis: GEOADD drivers lng lat driver_id
  → Store in DB: UPDATE drivers SET cell_id = X WHERE id = Y

Rider requests cab:
  → GEOSEARCH drivers FROMLONLAT lng lat BYRADIUS 2 km COUNT 10
  → Returns nearest 10 driver IDs in <1ms

Surge pricing check:
  → Count drivers in S2 cell at level 12 (~12km)
  → If count < threshold → apply surge multiplier
```
