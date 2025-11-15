"""
Web Crawler — Runnable POC

Demonstrates:
  - Priority Queue (URL scheduling)
  - Bloom Filter (URL deduplication)
  - Fetcher (HTTP download)
  - Extractor (URL parsing from HTML)
  - Scheduler (recrawl timing)
  - Rate Limiter (politeness per domain)

This is a LOCAL simulation — no Redis/Kafka/S3.
Real production would replace each class with distributed versions.

Run: python crawler.py
"""

import heapq
import hashlib
import time
import random
import math
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass(order=True)
class UrlTask:
    priority: int           # lower = higher priority (1=news, 3=static)
    scheduled_at: float     # unix timestamp — when to crawl
    url: str = field(compare=False)
    domain: str = field(compare=False)
    domain_type: str = field(compare=False, default="static")

# ── Bloom Filter ──────────────────────────────────────────────────────────────

class BloomFilter:
    """
    Probabilistic set — fast membership check.
    O(1) lookup, 1% false positive rate.
    Never says "not seen" when URL was actually seen.

    Uses k hash functions over a bit array of size m.
    """
    def __init__(self, capacity: int = 1_000_000, fp_rate: float = 0.01):
        # m = number of bits needed
        self.m = int(-capacity * math.log(fp_rate) / (math.log(2) ** 2))
        # k = number of hash functions
        self.k = int((self.m / capacity) * math.log(2))
        self.bits = bytearray(self.m // 8 + 1)
        self.count = 0
        print(f"[BloomFilter] bits={self.m:,}  hash_functions={self.k}  "
              f"size={self.m // 8 // 1024} KB  capacity={capacity:,}")

    def _hashes(self, item: str):
        """Generate k different hash positions for the item."""
        result = []
        for i in range(self.k):
            h = int(hashlib.md5(f"{i}:{item}".encode()).hexdigest(), 16)
            result.append(h % self.m)
        return result

    def add(self, item: str):
        for pos in self._hashes(item):
            self.bits[pos // 8] |= (1 << (pos % 8))
        self.count += 1

    def contains(self, item: str) -> bool:
        return all(
            self.bits[pos // 8] & (1 << (pos % 8))
            for pos in self._hashes(item)
        )

# ── Priority Queue ─────────────────────────────────────────────────────────────

class PriorityQueue:
    """
    Min-heap: lowest priority number = highest urgency.
    news(1) pops before sports(2) before static(3).
    """
    def __init__(self):
        self._heap: List[UrlTask] = []

    def push(self, task: UrlTask):
        heapq.heappush(self._heap, task)

    def pop(self) -> Optional[UrlTask]:
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek_scheduled_at(self) -> Optional[float]:
        return self._heap[0].scheduled_at if self._heap else None

    def size(self) -> int:
        return len(self._heap)

# ── DNS Resolver (with cache) ─────────────────────────────────────────────────

class DnsResolver:
    """
    Simulates DNS lookup with caching.
    Real version: Redis with TTL=300s.
    """
    def __init__(self):
        self._cache: Dict[str, tuple] = {}   # domain → (ip, expires_at)
        self.hits = 0
        self.misses = 0

    def resolve(self, domain: str) -> str:
        now = time.time()
        if domain in self._cache:
            ip, expires = self._cache[domain]
            if now < expires:
                self.hits += 1
                return ip

        # Simulate DNS lookup (real: socket.getaddrinfo)
        fake_ip = f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"
        self._cache[domain] = (fake_ip, now + 300)  # TTL = 5 minutes
        self.misses += 1
        return fake_ip

# ── Rate Limiter (politeness) ─────────────────────────────────────────────────

class DomainRateLimiter:
    """
    Token bucket per domain.
    Default: 1 request/sec per domain = polite crawling.
    """
    def __init__(self, rps: float = 1.0):
        self.rps = rps
        self.tokens: Dict[str, float] = defaultdict(float)
        self.last_check: Dict[str, float] = {}

    def can_crawl(self, domain: str) -> bool:
        now = time.time()
        elapsed = now - self.last_check.get(domain, now)
        self.tokens[domain] = min(1.0, self.tokens[domain] + elapsed * self.rps)
        self.last_check[domain] = now

        if self.tokens[domain] >= 1.0:
            self.tokens[domain] -= 1.0
            return True
        return False

# ── Fetcher ───────────────────────────────────────────────────────────────────

class Fetcher:
    """
    Simulates HTTP fetch.
    Real version: aiohttp with timeout, retries, robots.txt check.
    """
    def fetch(self, url: str, ip: str) -> Optional[str]:
        # Simulate occasional failures
        if random.random() < 0.05:   # 5% failure rate
            return None

        # Simulate HTML with embedded links
        domain = urlparse(url).netloc
        fake_links = [
            f"https://{domain}/article/{random.randint(1, 9999)}",
            f"https://{domain}/section/{random.randint(1, 99)}",
            f"https://{domain}/page/{random.randint(1, 999)}",
        ]
        html = f"""
        <html><body>
          <a href="{fake_links[0]}">Link 1</a>
          <a href="{fake_links[1]}">Link 2</a>
          <a href="{fake_links[2]}">Link 3</a>
          <p>Content of {url} fetched from {ip}</p>
        </body></html>
        """
        return html

# ── Extractor ─────────────────────────────────────────────────────────────────

class Extractor:
    """
    Parses HTML — extracts child URLs and content checksum.
    Real version: BeautifulSoup / lxml.
    """
    def extract_urls(self, html: str, base_url: str) -> List[str]:
        import re
        hrefs = re.findall(r'href="([^"]+)"', html)
        urls = []
        for href in hrefs:
            if href.startswith("http"):
                urls.append(href)
            elif href.startswith("/"):
                urls.append(urljoin(base_url, href))
        return urls

    def checksum(self, html: str) -> str:
        """MD5 of page content — used for duplicate detection."""
        return hashlib.md5(html.encode()).hexdigest()

# ── Content Storage (simulated S3) ────────────────────────────────────────────

class ContentStorage:
    def __init__(self):
        self.stored: Dict[str, str] = {}   # checksum → url
        self.saved_count = 0
        self.duplicate_count = 0

    def save(self, url: str, checksum: str, html: str) -> bool:
        if checksum in self.stored:
            self.duplicate_count += 1
            return False   # duplicate content
        self.stored[checksum] = url
        self.saved_count += 1
        return True        # saved to "S3"

# ── Scheduler ─────────────────────────────────────────────────────────────────

class Scheduler:
    """
    Determines crawl frequency per domain type.
    Recrawls: news every 1h, sports every 24h, static every 7d.
    """
    INTERVALS = {
        "news":   timedelta(hours=1),
        "sports": timedelta(hours=24),
        "static": timedelta(days=7),
    }

    def next_crawl_time(self, domain_type: str, fail_count: int = 0) -> float:
        interval = self.INTERVALS.get(domain_type, timedelta(days=7))
        # Exponential backoff on failures
        if fail_count > 0:
            interval = interval * (2 ** min(fail_count, 5))
        return (datetime.now() + interval).timestamp()

    def priority(self, domain_type: str) -> int:
        return {"news": 1, "sports": 2, "static": 3}.get(domain_type, 3)

# ── Main Crawler ──────────────────────────────────────────────────────────────

class WebCrawler:
    def __init__(self):
        self.queue       = PriorityQueue()
        self.bloom       = BloomFilter(capacity=100_000, fp_rate=0.01)
        self.dns         = DnsResolver()
        self.rate_limiter = DomainRateLimiter(rps=2.0)   # 2 req/sec per domain
        self.fetcher     = Fetcher()
        self.extractor   = Extractor()
        self.storage     = ContentStorage()
        self.scheduler   = Scheduler()
        self.crawled     = 0
        self.skipped     = 0

    def seed(self, urls: List[tuple]):
        """Load initial URLs. Each tuple: (url, domain_type)"""
        for url, domain_type in urls:
            self._enqueue(url, domain_type, priority_override=0)  # seed = highest priority
        print(f"[Crawler] Seeded {len(urls)} URLs. Queue size: {self.queue.size()}")

    def _enqueue(self, url: str, domain_type: str, priority_override: int = None):
        if self.bloom.contains(url):
            return   # already seen

        domain = urlparse(url).netloc
        priority = priority_override if priority_override is not None else self.scheduler.priority(domain_type)
        task = UrlTask(
            priority=priority,
            scheduled_at=time.time(),
            url=url,
            domain=domain,
            domain_type=domain_type
        )
        self.bloom.add(url)
        self.queue.push(task)

    def run(self, max_pages: int = 20):
        print(f"\n[Crawler] Starting crawl — max {max_pages} pages\n")
        while self.crawled < max_pages and self.queue.size() > 0:
            task = self.queue.pop()
            if not task:
                break

            # Politeness check
            if not self.rate_limiter.can_crawl(task.domain):
                time.sleep(0.1)

            # DNS resolve
            ip = self.dns.resolve(task.domain)

            # Fetch
            html = self.fetcher.fetch(task.url, ip)
            if not html:
                print(f"  [FAILED]  {task.url}")
                self.skipped += 1
                continue

            # Dedup content
            checksum = self.extractor.checksum(html)
            saved = self.storage.save(task.url, checksum, html)

            status = "SAVED " if saved else "DUPL  "
            print(f"  [{status}] [{task.domain_type:6}] {task.url[:60]}")
            self.crawled += 1

            # Extract child URLs and enqueue
            child_urls = self.extractor.extract_urls(html, task.url)
            for child_url in child_urls:
                self._enqueue(child_url, task.domain_type)

        self._stats()

    def _stats(self):
        print(f"""
[Crawler] Done
  Pages crawled:     {self.crawled}
  Pages skipped:     {self.skipped}
  Content saved:     {self.storage.saved_count}
  Duplicates found:  {self.storage.duplicate_count}
  DNS cache hits:    {self.dns.hits}
  DNS cache misses:  {self.dns.misses}
  Bloom filter size: {self.bloom.count:,} items
  Queue remaining:   {self.queue.size()}
""")


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    crawler = WebCrawler()

    # Seed URLs — (url, domain_type)
    seed_urls = [
        ("https://cnn.com/",           "news"),
        ("https://bbc.com/news",       "news"),
        ("https://espn.com/",          "sports"),
        ("https://nba.com/scores",     "sports"),
        ("https://wikipedia.org/",     "static"),
        ("https://python.org/docs",    "static"),
    ]

    crawler.seed(seed_urls)
    crawler.run(max_pages=30)
