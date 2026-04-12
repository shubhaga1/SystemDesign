#!/usr/bin/env python3
"""
One-time script to seed the revision DB with everything learned so far.
Run once: python seed.py
"""

import json
from datetime import date, timedelta
from pathlib import Path

DB_FILE = Path(__file__).parent / "revision_db.json"
SCHEDULE = [1, 3, 7]

def make_item(id, topic, category, note, file_ref, learned_days_ago):
    learned = date.today() - timedelta(days=learned_days_ago)
    revisions = []
    for d in SCHEDULE:
        due = learned + timedelta(days=d)
        done = due < date.today()
        revisions.append({
            "due": str(due),
            "done": done,
            "result": "✅" if done else None
        })
    return {
        "id": id, "topic": topic, "category": category,
        "note": note, "file": file_ref,
        "learned": str(learned), "revisions": revisions, "buried": False
    }

items = [
    # ── ENCRYPTION (learned ~1 day ago) ───────────────────────────────────────
    make_item(1,  "Symmetric AES — Fernet vs AES-256-GCM",
              "Encryption", "Fernet=AES128+HMAC easy API. GCM=256bit production. IV/nonce must be random every time",
              "SystemDesign/concepts/system-design/encryption/python/01_symmetric_aes.py", 1),

    make_item(2,  "RSA — asymmetric math, key gen, OAEP",
              "Encryption", "n=p×q public. Private=only if you know p,q. OAEP padding always. Max 190 bytes encrypt",
              "SystemDesign/concepts/system-design/encryption/python/02_asymmetric_rsa.py", 1),

    make_item(3,  "HTTPS TLS 1.2 handshake — RSA+AES hybrid",
              "Encryption", "RSA shares pre-master secret → both derive AES session key. RSA once, AES forever after",
              "SystemDesign/concepts/system-design/encryption/python/03_https_handshake.py", 1),

    make_item(4,  "RSA vs ECC — ECDH forward secrecy",
              "Encryption", "ECC-256=RSA-3072 security. ECDHE=ephemeral key per session=forward secrecy. TLS1.3 requires it",
              "SystemDesign/concepts/system-design/encryption/python/04_rsa_vs_ecc.py", 1),

    make_item(5,  "DEK/KEK pattern — AWS KMS simulation",
              "Encryption", "DEK=AES key per record. KEK=RSA wraps DEK. Rotate: re-wrap DEKs only. DB has cipher+wrapped DEK",
              "SystemDesign/concepts/system-design/encryption/python/05_dek_kek.py", 1),

    # ── SYSTEM DESIGN — WEB CRAWLER (today) ───────────────────────────────────
    make_item(6,  "Web Crawler — components and flow",
              "SystemDesign", "Scheduler→Kafka→Workers→DNS→Fetcher→Extractor→BloomFilter→Checksum→S3",
              "SystemDesign/concepts/system-design/web-crawler/README.md", 0),

    make_item(7,  "Web Crawler — capacity: 100TB not 10PB",
              "SystemDesign", "1B×100KB=100TB. /7days=14TB/day. /86400=160MB/sec. Common mistake: 10PB is 100x wrong",
              "SystemDesign/concepts/system-design/web-crawler/README.md", 0),

    make_item(8,  "Bloom Filter — sizing and why not HashSet",
              "SystemDesign", "1B URLs=1.2GB RAM (vs HashSet=100GB). 1% FP=occasionally re-crawl (acceptable). k=7 hash functions",
              "SystemDesign/concepts/system-design/web-crawler/lld.md", 0),

    make_item(9,  "Cassandra vs MySQL vs Redis for URL DB",
              "SystemDesign", "MySQL=single master bottleneck. Redis=200GB RAM too expensive. Cassandra=distributed writes, cheap disk",
              "SystemDesign/concepts/system-design/web-crawler/notes_deep_dive.md", 0),

    make_item(10, "Kafka priority — separate topics per tier",
              "SystemDesign", "Kafka is FIFO not priority. 3 topics: news/sports/static. Weighted poll 5:2:1 prevents starvation",
              "learning-journal/09-kafka/04_priority_queue_poc.py", 0),

    make_item(11, "K8s CronJob + Deployment + HPA",
              "K8s", "CronJob=scheduler every min. Deployment=N worker replicas. HPA=auto-scale on Kafka lag metric",
              "learning-journal/03-docker-k8s/06_k8s_poc.py", 0),

    make_item(12, "DNS cache TTL = 5 min why",
              "SystemDesign", "CDN rotates IPs for load balance. Cache forever=wrong IP. 50ms per lookup × 10K = saved. 300s safe TTL",
              "SystemDesign/concepts/system-design/web-crawler/notes_deep_dive.md", 0),

    # ── DSA — QUEUE (today) ───────────────────────────────────────────────────
    make_item(13, "Queue API — ArrayDeque not LinkedList",
              "DSA", "offer/poll/peek. ArrayDeque=cache friendly faster. LinkedList=extra pointer overhead per node",
              "algorithms/queue/01_QueueBasics.java", 0),

    make_item(14, "BFS level order — snapshot queue.size()",
              "DSA", "int size=queue.size() BEFORE for loop. Without snapshot: size grows as you add children mid-loop",
              "algorithms/queue/01_QueueBasics.java", 0),

    make_item(15, "PriorityQueue — min heap, max heap, custom",
              "DSA", "Default=min. reverseOrder()=max. Comparator.comparingInt(freq::get)=custom by map value",
              "algorithms/queue/02_PriorityQueue.java", 0),

    make_item(16, "Kth Largest — min heap of size k",
              "DSA", "offer all, poll when size>k (removes smallest). peek()=kth largest. O(nlogk) better than O(nlogn) sort",
              "algorithms/queue/02_PriorityQueue.java", 0),

    make_item(17, "Top K Frequent — freq map + min heap by freq",
              "DSA", "HashMap count freq. MinHeap by freq value. Poll when size>k removes least frequent. O(nlogk)",
              "algorithms/queue/02_PriorityQueue.java", 0),

    make_item(18, "Merge K Sorted Lists — PQ + push next",
              "DSA", "Seed heap with all heads. Poll min → add to result → push node.next. O(nlogk)",
              "algorithms/queue/02_PriorityQueue.java", 0),

    make_item(19, "Sliding Window Maximum — monotonic Deque",
              "DSA", "Store INDICES not values. pollLast if nums[dq.back]<=nums[i] (useless). pollFirst if outside window",
              "algorithms/queue/03_Deque.java", 0),

    make_item(20, "Rotting Oranges — multi-source BFS",
              "DSA", "Seed queue with ALL rotten oranges at t=0. Single-source would give wrong time (processes sequentially)",
              "algorithms/queue/04_InterviewPatterns.java", 0),

    make_item(21, "Meeting Rooms II — sort+min heap of ends",
              "DSA", "Sort by start. Min heap of end times. If heap.peek()<=start → reuse room (poll+offer). heap.size()=answer",
              "algorithms/queue/02_PriorityQueue.java", 0),

    # ── SQL (learned ~3 days ago) ─────────────────────────────────────────────
    make_item(22, "SQL DDL/DML/DQL — CREATE INSERT SELECT",
              "SQL", "DDL=structure(CREATE/ALTER/DROP). DML=data(INSERT/UPDATE/DELETE). DQL=query(SELECT)",
              "SystemDesign/concepts/sql/00_fundamentals.sql", 3),

    make_item(23, "WHERE vs HAVING — before/after GROUP BY",
              "SQL", "WHERE filters rows BEFORE grouping. HAVING filters groups AFTER. WHERE cannot use agg functions",
              "SystemDesign/concepts/sql/01_basics.sql", 3),

    make_item(24, "PIVOT — CASE WHEN rows to columns",
              "SQL", "SUM(CASE WHEN category='A' THEN amount END) AS A. Group by date. Each category becomes a column",
              "SystemDesign/concepts/sql/02_pivot.sql", 3),

    make_item(25, "NULL — IS NULL not = NULL, never empty string",
              "SQL", "= NULL always returns nothing. IS NULL correct. '' is empty string, not null. CASE WHEN IS NULL",
              "SystemDesign/concepts/sql/03_ddl_dml.sql", 3),

    # ── KAFKA (learned ~2 days ago) ───────────────────────────────────────────
    make_item(26, "Kafka KRaft — no Zookeeper, Kafka 3.3+",
              "Kafka", "Raft consensus built in. One system not two. 10x more partitions. Kafka 4.0 drops ZK entirely",
              "learning-journal/09-kafka/05_kafka_alternatives.py", 0),

    make_item(27, "Kafka vs RabbitMQ vs Redis Streams",
              "Kafka", "Kafka=stream/replay/high-throughput. RabbitMQ=task queue/priority/push. Redis=simple/already in Redis",
              "learning-journal/09-kafka/05_kafka_alternatives.py", 0),

    # ── PYTHON (today) ────────────────────────────────────────────────────────
    make_item(28, "venv — activate prepends PATH, not dir-based",
              "Python", "source activate → .venv/bin prepended to PATH. Works from any folder in terminal. deactivate restores",
              "SystemDesign/concepts/python/01_venv.md", 0),
]

db = {"items": items, "next_id": len(items) + 1}
DB_FILE.write_text(json.dumps(db, indent=2, default=str))
print(f"✅ Seeded {len(items)} items into {DB_FILE}")
print("Now run: python revise.py")
