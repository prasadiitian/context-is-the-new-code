"""selection.py -- choose what enters the context."""
from engine.assembler import ContextItem
from engine.retrieval import words

WEIGHTS = {"relevance": 0.6, "recency": 0.2, "source": 0.2}
SOURCE_VALUE = {"tool result": 0.9, "state": 0.8, "retrieved": 0.8,
                "memory": 0.7, "summary": 0.6, "history": 0.3}


def expand(query: str, glossary: dict[str, str]) -> str:
    """Add the domain's own words for what the user asked."""
    extra = [glossary[w] for w in words(query) if w in glossary]
    return " ".join([query] + extra)


def relevance(query: str, text: str) -> float:
    """Share of the query's words that the text contains."""
    wanted = set(words(query))
    if not wanted:
        return 0.0
    return len(wanted & set(words(text))) / len(wanted)


def recency(item: ContextItem) -> float:
    """1.0 for the newest item, falling towards 0 with age."""
    return 1 / (1 + item.meta.get("age", 0))


def score(item: ContextItem, query: str, weights=WEIGHTS) -> float:
    return (weights["relevance"] * relevance(query, item.content)
            + weights["recency"] * recency(item)
            + weights["source"] * SOURCE_VALUE.get(item.source, 0.5))


def select(items, query, budget, quotas=None):
    """Must-keep items first, then the best of the rest that fit.

    Returns (kept, dropped), each in the original order.
    """
    quotas = quotas or {}
    order = sorted(
        range(len(items)),
        key=lambda i: (items[i].priority != 1,
                       -score(items[i], query)))
    keep, used, spent = set(), 0, {}
    for i in order:
        item = items[i]
        cap = quotas.get(item.source, budget)
        in_quota = spent.get(item.source, 0) + item.tokens <= cap
        if used + item.tokens <= budget and (
                item.priority == 1 or in_quota):
            keep.add(i)
            used += item.tokens
            spent[item.source] = (spent.get(item.source, 0)
                                  + item.tokens)
    kept = [it for i, it in enumerate(items) if i in keep]
    dropped = [it for i, it in enumerate(items) if i not in keep]
    return kept, dropped
