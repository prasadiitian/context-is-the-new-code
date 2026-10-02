"""ch05_demo.py -- retrieval that knows what is still in force."""
from engine.retrieval import (Index, as_context, dedupe, in_force,
                              split)
from engine.tokens import get_counter
from support_data import POLICIES, REQUEST, TODAY

counter = get_counter()
index = Index()
for policy in POLICIES:
    meta = {"title": policy["title"],
            "effective": policy["effective"],
            "superseded": policy["superseded"]}
    for chunk in split(policy["id"], policy["text"], meta):
        index.add(chunk)


def show(title, hits):
    print(title)
    for score, chunk in hits:
        print(f"  {score:5.2f}  {chunk.doc_id:14}"
              f"{chunk.text[:38]}...")
    tokens = counter.count(as_context(hits))
    print(f"  {len(hits)} excerpts, {tokens} tokens")
    print()


print(f"query: {REQUEST}")
print()
naive = index.search(REQUEST, k=5)
show("1. top five by score alone", naive)

current = index.search(REQUEST, k=5, where=in_force(TODAY))
show("2. only documents in force today", current)

strong = [hit for hit in current if hit[0] >= 0.5 * current[0][0]]
final = dedupe(strong)
show("3. within half of the best score, no repeats", final)

print(as_context(final))
