"""caching.py -- pay less for tokens you send again."""
import time

# How often each source changes: 0 = never, 4 = every call.
VOLATILITY = {"instructions": 0, "tool definitions": 0, "memory": 1,
              "today": 1, "summary": 2, "state": 2, "request": 2,
              "retrieved": 3, "history": 3, "tool result": 4}


def order_for_cache(items):
    """Stable material first, so the unchanged prefix is long."""
    return sorted(items,
                  key=lambda it: VOLATILITY.get(it.source, 3))


def shared_prefix(previous: list[str], current: list[str]) -> int:
    """How many leading parts two requests have in common."""
    same = 0
    for a, b in zip(previous, current):
        if a != b:
            break
        same += 1
    return same


class CacheMeter:
    """Counts the tokens a prefix cache would and would not serve."""

    def __init__(self, counter):
        self.counter = counter
        self.previous: list[str] = []
        self.cached = 0
        self.fresh = 0

    def record(self, parts: list[str]) -> tuple[int, int]:
        same = shared_prefix(self.previous, parts)
        hit = sum(self.counter.count(p) for p in parts[:same])
        miss = sum(self.counter.count(p) for p in parts[same:])
        self.cached += hit
        self.fresh += miss
        self.previous = list(parts)
        return hit, miss

    def cost(self, price_in: float, price_cached: float) -> float:
        """Input cost. Prices are per million tokens."""
        return (self.fresh * price_in
                + self.cached * price_cached) / 1_000_000


class TTLCache:
    """Remember a computed result for a limited time."""

    def __init__(self, ttl_seconds: float, clock=time.time):
        self.ttl = ttl_seconds
        self.clock = clock
        self.store: dict = {}
        self.hits = 0
        self.misses = 0

    def get(self, key, compute):
        now = self.clock()
        if key in self.store and now - self.store[key][0] < self.ttl:
            self.hits += 1
            return self.store[key][1]
        self.misses += 1
        value = compute()
        self.store[key] = (now, value)
        return value
