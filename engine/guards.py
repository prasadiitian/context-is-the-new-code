"""guards.py -- catch bad context before the model reads it."""
import re

from engine.compression import head_tail

SUSPICIOUS = [
    r"ignore (all |any )?(previous|prior|above) (instructions|rules)",
    r"disregard (the|your) (instructions|rules|system prompt)",
    r"you are now",
    r"new instructions",
    r"do not (tell|inform) the (user|customer)",
    r"reveal (your|the) (instructions|system prompt)",
]
UNTRUSTED = {"retrieved", "tool result", "memory", "history",
             "summary"}


def scan(text: str) -> list[str]:
    """Phrases that read like instructions aimed at the model."""
    lower = text.lower()
    found = []
    for pattern in SUSPICIOUS:
        match = re.search(pattern, lower)
        if match:
            found.append(match.group(0))
    return found


def screen(items):
    """Quarantine untrusted items that carry instructions.

    Returns (clean items, flags).
    """
    clean, flags = [], []
    for item in items:
        hits = scan(item.content) if item.source in UNTRUSTED else []
        if hits:
            flags.append(f"quarantined {item.source}: '{hits[0]}'")
        else:
            clean.append(item)
    return clean, flags


def fence(item) -> str:
    """Write untrusted content so it reads as data, not orders."""
    body = item.content.replace("</", "< /")
    tag = item.source
    return f'<{tag} trust="data only">\n{body}\n</{tag}>'


def conflicts(items) -> list[str]:
    """Places where two items give different numbers for one thing."""
    seen: dict[tuple, str] = {}
    found = []
    for item in items:
        triples = re.findall(r"(\w+) (\d+) (\w+)",
                             item.content.lower())
        for before, number, after in triples:
            key = (before, after)
            first = seen.setdefault(key, number)
            if first != number:
                found.append(f"'{before} {first} {after}' against "
                             f"'{before} {number} {after}'")
    return sorted(set(found))


class ContextOverflow(Exception):
    """Even the must-keep items do not fit."""


def enforce(items, budget, counter, clip_to=60):
    """Bring a context under budget, one careful step at a time.

    Returns (items, actions taken).
    """
    items, actions = list(items), []

    def total():
        return sum(item.tokens for item in items)

    # 1. Clip oversized items, largest first. Never the request.
    for item in sorted(items, key=lambda it: -it.tokens):
        if total() <= budget:
            break
        if item.tokens > clip_to and item.source != "request":
            before = item.tokens
            item.content = head_tail(item.content, clip_to, counter)
            item.tokens = counter.count(item.content)
            actions.append(f"clipped {item.source} "
                           f"({before} to {item.tokens} tokens)")
    # 2. Drop optional items, largest first.
    optional = sorted((it for it in items if it.priority != 1),
                      key=lambda it: -it.tokens)
    for item in optional:
        if total() <= budget:
            break
        items.remove(item)
        actions.append(f"dropped {item.source} "
                       f"({item.tokens} tokens)")
    # 3. Refuse loudly instead of sending a broken context.
    if total() > budget:
        raise ContextOverflow(
            f"{total()} tokens of must-keep context, "
            f"budget {budget}")
    return items, actions
