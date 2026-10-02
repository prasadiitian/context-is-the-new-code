"""ch10_demo.py -- the same 20 steps in two layouts."""
from engine.caching import CacheMeter, TTLCache
from engine.tokens import get_counter
from support_tools import check_outage

counter = get_counter()

INSTRUCTIONS = "You are the support agent. " * 40
TOOLS = "tool definition text. " * 50
MEMORY = "Wants follow-up by email. " * 4
REQUEST = "Can I cancel and get my money back?"
RESULT = "Result of step {n}: " + "detail " * 110

# Example prices per million tokens. Use your provider's rates.
PRICE_IN, PRICE_CACHED = 3.00, 0.30


def run(layout) -> CacheMeter:
    meter = CacheMeter(counter)
    results = []
    for step in range(20):
        meter.record(layout(step, results))
        results.append(RESULT.format(n=step))
    return meter


def clock_first(step, results):
    """A timestamp at the top: every call starts differently."""
    stamp = f"Current time: 10:{step:02}:00"
    return [stamp, INSTRUCTIONS, TOOLS, MEMORY, REQUEST, *results]


def stable_first(step, results):
    """Fixed parts first; new material only ever added at the end."""
    return [INSTRUCTIONS, TOOLS, MEMORY, "Date: 10 March 2026",
            REQUEST, *results]


print(f"{'layout':14}{'fresh':>9}{'cached':>9}{'input cost':>12}")
for layout in (clock_first, stable_first):
    meter = run(layout)
    price = meter.cost(PRICE_IN, PRICE_CACHED)
    print(f"{layout.__name__:14}{meter.fresh:9,}{meter.cached:9,}"
          f"{'$' + format(price, '.2f'):>12}")

# A result cache: the same lookup inside its lifetime runs once.
now = [0.0]
cache = TTLCache(ttl_seconds=300, clock=lambda: now[0])
for minute in (0, 1, 2, 6):
    now[0] = minute * 60
    cache.get(("check_outage", "560001"),
              lambda: check_outage("560001"))
print()
print(f"outage lookups: 4 requests, {cache.misses} real calls, "
      f"{cache.hits} served from cache")
