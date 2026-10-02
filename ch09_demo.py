"""ch09_demo.py -- four ways to compress, measured."""
import json

from engine.compression import (compact, extract, head_tail, lost,
                                squeeze)
from engine.conversation import Conversation
from engine.model import get_model
from engine.selection import expand
from engine.tokens import get_counter
from support_data import (CUSTOMER, GLOSSARY, POLICIES, REQUEST,
                          billing_record, history)

counter = get_counter()
rows = []


def measure(name, before, after):
    b, a = counter.count(before), counter.count(after)
    rows.append((name, b, a))


# 1. Remove repeats: free and lossless.
texts = [p["text"] for p in POLICIES if "refund" in p["id"]
         or p["id"] in ("faq-2024", "terms-2024")]
unique = squeeze(texts)
measure(f"squeeze ({len(texts)} texts to {len(unique)})",
        "\n".join(texts), "\n".join(unique))

# 2. Keep only the sentences that bear on the request.
handbook = " ".join(p["text"] for p in POLICIES
                    if not p["superseded"])
query = expand(REQUEST, GLOSSARY)
picked = extract(handbook, query, keep=2)
measure("extract (2 sentences)", handbook, picked)

# 3. Keep both ends of something that cannot be shaped.
raw = json.dumps(billing_record(CUSTOMER), indent=1)
ends = head_tail(raw, limit=40, counter=counter)
measure("head_tail (raw record)", raw, ends)

# 4. Summarise old turns with a model.
chat = Conversation(counter)
for role, text in history():
    chat.add(role, text)
before = "\n".join(turn.content for turn in chat.turns)
model = get_model(["""\
- Router light blinked orange, later solid white; speed is slow.
- Customer restarted the router several times; it keeps dropping.
- Line test from our side shows a weak signal.
- Fault logged; an engineer will inspect the line.
- Customer says they signed up three weeks ago.
- Customer wants follow-up by email, not phone calls."""])
folded = compact(chat, model, keep_tokens=150)
after = chat.summary + "\n" + "\n".join(t.content for t in chat.turns)
measure(f"summarise ({folded} turns folded)", before, after)

print(f"{'technique':34}{'before':>7}{'after':>7}{'saved':>7}")
for name, b, a in rows:
    print(f"{name:34}{b:7}{a:7}{1 - a / b:7.0%}")

print()
print("extract kept:")
print(" ", picked)
print()
print(f"summary ({model.name} model):")
print(chat.summary)
print()
must_keep = ["email", "fault logged", "three weeks|3 weeks"]
careless = "Customer has router problems. Fault logged."
print("missing from the summary above:",
      lost(chat.summary, must_keep) or "nothing")
print("missing from a careless one:  ",
      lost(careless, must_keep))
