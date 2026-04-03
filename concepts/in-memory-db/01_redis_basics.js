/**
 * Redis Basics — String, Hash, List, Set, SortedSet
 *
 * Requires: Redis running locally
 *   docker-compose up -d
 *
 * Run: node 01_redis_basics.js
 */

const { createClient } = require('redis');

async function main() {
    const client = createClient({ url: 'redis://localhost:6379' });

    client.on('error', err => console.error('Redis error:', err));
    await client.connect();
    console.log('Connected to Redis\n');

    // ─── 1. STRING — simplest type ────────────────────────────────────────────
    console.log('=== STRING ===');

    await client.set('username', 'shubham');
    const name = await client.get('username');
    console.log('GET username:', name);                        // shubham

    // SET with expiry (TTL = time to live in seconds)
    await client.set('session:abc123', 'user:42', { EX: 60 }); // expires in 60s
    const ttl = await client.ttl('session:abc123');
    console.log('TTL session:abc123:', ttl, 'seconds');

    // Atomic counter — INCR is atomic, safe for concurrent requests
    await client.set('page:views', 0);
    await client.incr('page:views');
    await client.incr('page:views');
    await client.incrBy('page:views', 10);
    console.log('Page views:', await client.get('page:views'));  // 12

    // ─── 2. HASH — object/map ─────────────────────────────────────────────────
    console.log('\n=== HASH (user profile) ===');

    await client.hSet('user:1', {
        name:  'Shubham',
        email: 'schmuck21@gmail.com',
        city:  'Mumbai',
        score: 95,
    });

    const user = await client.hGetAll('user:1');
    console.log('hGetAll user:1:', user);

    const email = await client.hGet('user:1', 'email');
    console.log('hGet email:', email);

    // Update one field without touching rest
    await client.hSet('user:1', 'city', 'Bangalore');
    console.log('Updated city:', await client.hGet('user:1', 'city'));

    // ─── 3. LIST — ordered, allows duplicates ─────────────────────────────────
    console.log('\n=== LIST (activity feed) ===');

    await client.del('feed:user1');
    await client.lPush('feed:user1', 'Logged in');           // add to LEFT (front)
    await client.lPush('feed:user1', 'Viewed dashboard');
    await client.lPush('feed:user1', 'Updated profile');
    await client.rPush('feed:user1', 'Logged out');          // add to RIGHT (end)

    const feed = await client.lRange('feed:user1', 0, -1);   // 0 to -1 = all
    console.log('Activity feed:', feed);
    console.log('Feed length:', await client.lLen('feed:user1'));

    // Queue pattern: RPUSH to add, LPOP to consume
    await client.rPush('queue:emails', 'email:1', 'email:2', 'email:3');
    const nextEmail = await client.lPop('queue:emails');
    console.log('Next to process:', nextEmail);                // email:1 (FIFO)

    // ─── 4. SET — unique members, no order ───────────────────────────────────
    console.log('\n=== SET (unique visitors) ===');

    await client.del('visitors:today');
    await client.sAdd('visitors:today', 'user:1', 'user:2', 'user:3', 'user:1'); // user:1 twice
    const count = await client.sCard('visitors:today');       // cardinality = count
    console.log('Unique visitors today:', count);              // 3 (not 4)

    const isMember = await client.sIsMember('visitors:today', 'user:2');
    console.log('user:2 visited?', isMember);                 // true

    // Set intersection — users in BOTH sets
    await client.sAdd('visitors:yesterday', 'user:2', 'user:4', 'user:5');
    const returning = await client.sInter(['visitors:today', 'visitors:yesterday']);
    console.log('Returning visitors:', returning);             // [user:2]

    // ─── 5. SORTED SET — unique members WITH a score, ordered by score ────────
    console.log('\n=== SORTED SET (leaderboard) ===');

    await client.del('leaderboard');
    await client.zAdd('leaderboard', [
        { score: 95,  value: 'Alice' },
        { score: 87,  value: 'Bob' },
        { score: 99,  value: 'Charlie' },
        { score: 72,  value: 'Diana' },
        { score: 87,  value: 'Eve' },
    ]);

    // Top 3 — ZRANGE with REV=true (highest first)
    const top3 = await client.zRangeWithScores('leaderboard', 0, 2, { REV: true });
    console.log('Top 3:');
    top3.forEach((e, i) => console.log(`  ${i+1}. ${e.value} — ${e.score}`));

    // Rank of a player (0-indexed from lowest, REV for highest)
    const rank = await client.zRevRank('leaderboard', 'Bob');  // 0 = top
    console.log('Bob rank (from top):', rank + 1);             // 3rd

    // Score of a player
    const score = await client.zScore('leaderboard', 'Charlie');
    console.log('Charlie score:', score);                      // 99

    // ─── Cleanup ─────────────────────────────────────────────────────────────
    await client.del('username', 'page:views', 'user:1', 'feed:user1',
                     'queue:emails', 'visitors:today', 'visitors:yesterday', 'leaderboard');

    await client.disconnect();
    console.log('\nDisconnected from Redis');
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
