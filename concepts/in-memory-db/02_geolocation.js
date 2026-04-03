/**
 * Redis Geolocation — GEOADD, GEODIST, GEOPOS, GEOSEARCH
 *
 * Use case: Uber-like "find nearest drivers"
 *           Swiggy-like "find restaurants within 3km"
 *
 * How it works internally:
 *   Redis encodes lat/lng as a 52-bit geohash integer
 *   Stored internally as a Sorted Set (score = geohash)
 *   Range queries = scan a geohash prefix = nearby points
 *
 * Requires: Redis running
 *   docker-compose up -d
 *
 * Run: node 02_geolocation.js
 */

const { createClient } = require('redis');

// ─── Sample data — Mumbai locations ───────────────────────────────────────────
// Format: [longitude, latitude, name]
// Note: Redis uses lng,lat order (not lat,lng like Google Maps)

const DRIVERS = [
    { lng: 72.8777, lat: 19.0760, id: 'driver:1', name: 'Rahul  (Bandra)' },
    { lng: 72.8296, lat: 18.9750, id: 'driver:2', name: 'Amit   (Dadar)' },
    { lng: 72.8659, lat: 19.1136, id: 'driver:3', name: 'Vijay  (Andheri)' },
    { lng: 72.8317, lat: 18.9890, id: 'driver:4', name: 'Suresh (Worli)' },
    { lng: 72.9081, lat: 19.1197, id: 'driver:5', name: 'Kiran  (Powai)' },
    { lng: 72.8258, lat: 18.9260, id: 'driver:6', name: 'Dev    (Parel)' },
];

const RESTAURANTS = [
    { lng: 72.8356, lat: 18.9676, id: 'rest:1', name: 'Trishna    (Fort)' },
    { lng: 72.8296, lat: 18.9500, id: 'rest:2', name: 'Mahesh     (Dadar)' },
    { lng: 72.8777, lat: 19.0760, id: 'rest:3', name: 'Pizza Place (Bandra)' },
    { lng: 72.8297, lat: 19.0330, id: 'rest:4', name: 'Chai Spot  (Santacruz)' },
    { lng: 72.8659, lat: 19.1200, id: 'rest:5', name: 'Biryani House (Andheri)' },
];

const USER_LOCATION = { lng: 72.8356, lat: 18.9700, name: 'User (Fort area)' };

async function main() {
    const client = createClient({ url: 'redis://localhost:6379' });
    client.on('error', err => console.error('Redis error:', err));
    await client.connect();
    console.log('Connected to Redis\n');

    // ─── 1. GEOADD — store locations ─────────────────────────────────────────
    console.log('=== 1. GEOADD — store driver locations ===');

    await client.del('drivers', 'restaurants');

    // Add all drivers to the geo set
    for (const d of DRIVERS) {
        await client.geoAdd('drivers', { longitude: d.lng, latitude: d.lat, member: d.id });
        console.log(`  Added ${d.name} at (${d.lng}, ${d.lat})`);
    }

    // Add all restaurants
    for (const r of RESTAURANTS) {
        await client.geoAdd('restaurants', { longitude: r.lng, latitude: r.lat, member: r.id });
    }
    console.log(`\n${DRIVERS.length} drivers, ${RESTAURANTS.length} restaurants added`);

    // ─── 2. GEOPOS — get stored coordinates ──────────────────────────────────
    console.log('\n=== 2. GEOPOS — retrieve coordinates ===');

    const positions = await client.geoPos('drivers', ['driver:1', 'driver:3']);
    positions.forEach((pos, i) => {
        if (pos) {
            const d = DRIVERS[i === 0 ? 0 : 2];
            console.log(`  ${d.name}: lng=${parseFloat(pos.longitude).toFixed(4)}, lat=${parseFloat(pos.latitude).toFixed(4)}`);
        }
    });

    // ─── 3. GEODIST — distance between two members ────────────────────────────
    console.log('\n=== 3. GEODIST — distance between two drivers ===');

    const distKm = await client.geoDist('drivers', 'driver:1', 'driver:2', 'km');
    const distMi = await client.geoDist('drivers', 'driver:1', 'driver:2', 'mi');
    console.log(`  driver:1 (Bandra) ↔ driver:2 (Dadar): ${parseFloat(distKm).toFixed(2)} km  /  ${parseFloat(distMi).toFixed(2)} mi`);

    const d1to5 = await client.geoDist('drivers', 'driver:1', 'driver:5', 'km');
    console.log(`  driver:1 (Bandra) ↔ driver:5 (Powai):  ${parseFloat(d1to5).toFixed(2)} km`);

    // ─── 4. GEOSEARCH — find nearby (the main use case) ──────────────────────
    console.log('\n=== 4. GEOSEARCH — find drivers near user ===');
    console.log(`  User is at: ${USER_LOCATION.name} (${USER_LOCATION.lng}, ${USER_LOCATION.lat})\n`);

    // Find all drivers within 5km radius, sorted by distance
    const nearbyDrivers = await client.geoSearch(
        'drivers',
        { longitude: USER_LOCATION.lng, latitude: USER_LOCATION.lat },
        { radius: 5, unit: 'km' },
        {
            SORT: 'ASC',          // closest first
            COUNT: 5,             // max 5 results
            WITHCOORD: true,      // include coordinates
            WITHDIST: true,       // include distance
        }
    );

    console.log(`  Drivers within 5km (sorted by distance):`);
    nearbyDrivers.forEach((driver, i) => {
        const info = DRIVERS.find(d => d.id === driver.member);
        const label = info ? info.name : driver.member;
        console.log(`    ${i + 1}. ${label.padEnd(25)} — ${parseFloat(driver.distance).toFixed(2)} km away`);
    });

    // Tighten radius to 2km
    const veryNear = await client.geoSearch(
        'drivers',
        { longitude: USER_LOCATION.lng, latitude: USER_LOCATION.lat },
        { radius: 2, unit: 'km' },
        { SORT: 'ASC', WITHDIST: true }
    );

    console.log(`\n  Drivers within 2km:`);
    if (veryNear.length === 0) {
        console.log('    None');
    } else {
        veryNear.forEach(d => {
            const info = DRIVERS.find(dr => dr.id === d.member);
            console.log(`    → ${info ? info.name : d.member} — ${parseFloat(d.distance).toFixed(2)} km`);
        });
    }

    // ─── 5. GEOSEARCH by member — "find restaurants near driver:2" ───────────
    console.log('\n=== 5. GEOSEARCH by member — restaurants near driver:2 ===');

    const driverPos = await client.geoPos('drivers', ['driver:2']);
    const dPos = driverPos[0];

    const nearRests = await client.geoSearch(
        'restaurants',
        { longitude: dPos.longitude, latitude: dPos.latitude },
        { radius: 3, unit: 'km' },
        { SORT: 'ASC', WITHDIST: true }
    );

    console.log(`  Restaurants within 3km of ${DRIVERS[1].name}:`);
    nearRests.forEach(r => {
        const info = RESTAURANTS.find(rest => rest.id === r.member);
        console.log(`    → ${info ? info.name : r.member} — ${parseFloat(r.distance).toFixed(2)} km`);
    });

    // ─── 6. Geohash — see how Redis encodes internally ────────────────────────
    console.log('\n=== 6. GEOHASH — internal encoding ===');

    const hashes = await client.geoHash('drivers', ['driver:1', 'driver:2', 'driver:3']);
    hashes.forEach((hash, i) => {
        const d = [DRIVERS[0], DRIVERS[1], DRIVERS[2]][i];
        console.log(`  ${d.name}: geohash = ${hash}`);
    });
    console.log('  Shared prefix = nearby location');
    console.log('  driver:1 and driver:3 share "te7u" — both in north Mumbai');

    // ─── 7. Real-world pattern — surge pricing zones ──────────────────────────
    console.log('\n=== 7. PATTERN — count drivers in a zone (surge pricing) ===');

    // Airport zone — drivers within 1km of Mumbai airport
    const AIRPORT = { lng: 72.8679, lat: 19.0896 };

    const atAirport = await client.geoSearch(
        'drivers',
        { longitude: AIRPORT.lng, latitude: AIRPORT.lat },
        { radius: 3, unit: 'km' },
        { SORT: 'ASC', WITHDIST: true }
    );

    console.log(`  Drivers near airport (within 3km): ${atAirport.length}`);
    atAirport.forEach(d => {
        const info = DRIVERS.find(dr => dr.id === d.member);
        console.log(`    → ${info ? info.name : d.member} — ${parseFloat(d.distance).toFixed(2)} km from airport`);
    });

    const surgePricing = atAirport.length < 2;
    console.log(`  Surge pricing active: ${surgePricing ? 'YES (low supply)' : 'NO (enough drivers)'}`);

    // ─── Cleanup ─────────────────────────────────────────────────────────────
    await client.del('drivers', 'restaurants');
    await client.disconnect();

    console.log('\n=== KEY TAKEAWAYS ===');
    console.log(`
  GEOADD  key lng lat member   → store a location
  GEODIST key m1 m2 unit       → distance between two stored points
  GEOPOS  key member           → get coordinates of a stored point
  GEOHASH key member           → get the geohash string
  GEOSEARCH key FROMLONLAT lng lat BYRADIUS r unit
                               → find members within radius

  Redis geo uses longitude,latitude order (opposite of Google Maps lat,lng)

  Internally: sorted set where score = 52-bit geohash integer
  → Range queries on the sorted set = nearby points = O(N+log M)

  Real use cases:
    Uber     → GEOSEARCH drivers near rider, show top 5
    Swiggy   → GEOSEARCH restaurants near user address
    Bumble   → GEOSEARCH profiles within X km
    Surge    → count drivers in zone, if < threshold → surge price
  `);
}

main().catch(err => {
    console.error('\nError — is Redis running?');
    console.error('Run: docker-compose up -d');
    console.error(err.message);
    process.exit(1);
});
