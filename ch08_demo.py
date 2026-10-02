"""ch08_demo.py -- newest-first against scored selection."""
from engine.assembler import ContextItem, render
from engine.selection import expand, score, select
from engine.tokens import get_counter
from support_data import CUSTOMER, GLOSSARY, REQUEST, history
from support_tools import lookup_account, search_policies

counter = get_counter()


def item(source, content, priority=2, **meta):
    made = ContextItem(source, content, priority, meta)
    made.tokens = counter.count(content)
    return made


query = expand(REQUEST, GLOSSARY)
print(f"selection query: {query}")

turns = history()
items = [item("today", "Today is 10 March 2026.", priority=1)]
for n, (role, text) in enumerate(turns):
    who = "Customer" if role == "user" else "Agent"
    items.append(item("history", f"{who}: {text}",
                      age=len(turns) - n))
items.append(item("memory",
                  "Wants follow-up by email, not by phone call."))
items.append(item("retrieved", search_policies(query)))
items.append(item("tool result", lookup_account(CUSTOMER)))
items.append(item("request", REQUEST, priority=1))

BUDGET = 220
total = sum(it.tokens for it in items)
print(f"{len(items)} candidates, {total} tokens, budget {BUDGET}")


def newest_first(items, budget):
    """The common default: fill the budget from the end."""
    kept, used = [], 0
    for it in reversed(items):
        if used + it.tokens <= budget:
            kept.append(it)
            used += it.tokens
    return list(reversed(kept))


def summary(title, kept):
    by_source = {}
    for it in kept:
        by_source[it.source] = by_source.get(it.source, 0) + 1
    used = sum(it.tokens for it in kept)
    print()
    print(f"{title}: {used} tokens")
    for source, count in by_source.items():
        print(f"  {source:12}{count} item(s)")


baseline = newest_first(items, BUDGET)
summary("newest first", baseline)

kept, dropped = select(items, query, BUDGET, quotas={"history": 60})
summary("scored selection", kept)

print()
print("history turns chosen by score:")
for it in kept:
    if it.source == "history":
        print(f"  {score(it, query):.2f}  {it.content[:52]}...")

print()
print("\n\n".join(render(it) for it in kept
                  if it.source != "history"))
