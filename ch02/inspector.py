"""inspector.py -- count, inspect and price a model request."""
import json

from sample_request import build


# --- Counting -----------------------------------------------------

class HeuristicCounter:
    """About four characters per token. Rough, no dependencies."""
    name = "heuristic (4 characters per token)"

    def count(self, text: str) -> int:
        return max(1, len(text) // 4)


class TiktokenCounter:
    """Exact counts for models that use an OpenAI tokenizer."""
    name = "tiktoken"

    def __init__(self, encoding: str = "o200k_base"):
        import tiktoken
        self.enc = tiktoken.get_encoding(encoding)

    def count(self, text: str) -> int:
        return len(self.enc.encode(text))


def get_counter():
    """Use a real tokenizer when one is installed and usable."""
    try:
        return TiktokenCounter()
    except Exception:
        return HeuristicCounter()


# --- Inspecting ---------------------------------------------------

def flatten(request) -> list[tuple[str, str]]:
    """Every part of a request as (source, text), in order."""
    parts = [("instructions", request["system"])]
    for tool in request.get("tools", []):
        parts.append(("tool definitions", json.dumps(tool)))
    for msg in request["messages"]:
        parts.append((msg["source"], msg["content"]))
    return parts


def inspect(request, counter) -> dict[str, int]:
    """Token count per source."""
    totals: dict[str, int] = {}
    for source, text in flatten(request):
        totals[source] = totals.get(source, 0) + counter.count(text)
    return totals


def report(totals, window, reserve_output) -> str:
    total = sum(totals.values())
    lines = []
    for source, n in sorted(totals.items(), key=lambda kv: -kv[1]):
        bar = "#" * round(30 * n / total)
        lines.append(f"{source:17}{n:6,}{n / total:7.1%}  {bar}")
    budget = window - reserve_output
    lines.append(f"{'total':17}{total:6,}")
    lines.append(f"input budget {budget:,} tokens, "
                 f"{total / budget:.1%} used")
    return "\n".join(lines)


# --- Pricing ------------------------------------------------------

def cost(tokens_in, tokens_out, price_in, price_out) -> float:
    """Cost of one call. Prices are per million tokens."""
    return (tokens_in * price_in
            + tokens_out * price_out) / 1_000_000


def agent_run(start, growth, steps) -> list[int]:
    """Input tokens at each step when nothing is ever removed."""
    return [start + growth * step for step in range(steps)]


if __name__ == "__main__":
    counter = get_counter()
    request = build()
    totals = inspect(request, counter)

    print(f"counter: {counter.name}")
    print(report(totals, window=128_000, reserve_output=4_000))

    # Example prices only. Look up your provider's current rates.
    PRICE_IN, PRICE_OUT = 3.00, 15.00
    start = sum(totals.values())
    inputs = agent_run(start, growth=800, steps=20)
    total_in = sum(inputs)
    total_out = 300 * len(inputs)
    print()
    print(f"step 1 input   {inputs[0]:8,} tokens")
    print(f"step 20 input  {inputs[-1]:8,} tokens")
    print(f"all 20 inputs  {total_in:8,} tokens")
    run = cost(total_in, total_out, PRICE_IN, PRICE_OUT)
    print(f"one task       ${run:.2f}")
    print(f"10,000 tasks   ${run * 10_000:,.0f}")
