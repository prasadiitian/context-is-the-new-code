"""ch07b_demo.py -- more memories than room, expiry and deletion."""
import os
from datetime import date

from engine.memory import MemoryStore, as_block
from support_data import CUSTOMER

PATH = "memory.json"
if os.path.exists(PATH):
    os.remove(PATH)
store = MemoryStore(PATH)

SAVED = [
    ("earlier refund", "Received a goodwill refund of one month "
     "after an outage.", "billing system", date(2025, 2, 1)),
    ("plan", "Moved from Fibre 100 to Fibre 300.",
     "billing system", date(2026, 2, 15)),
    ("contact", "Wants follow-up by email, not by phone call.",
     "stated by customer", date(2026, 3, 10)),
    ("open fault", "Line fault logged; engineer to inspect the "
     "line.", "fault system", date(2026, 3, 10)),
    ("refund", "Asked for a refund at 23 days; outside the 14-day "
     "refund window.", "account lookup and policy",
     date(2026, 3, 10)),
    ("refund complaint", "Said the refund refusal was unfair and "
     "asked for a review.", "stated by customer",
     date(2026, 3, 12)),
]
for key, text, source, day in SAVED:
    store.remember(CUSTOMER, key, text, source, day)

today = date(2026, 3, 18)
question = "Why was my refund refused when I got one last year?"
print(f"question: {question}")

for k, age in ((3, 365), (3, 730)):
    found = store.recall(CUSTOMER, question, today, k=k,
                         max_age_days=age)
    print()
    print(f"k={k}, max age {age} days: "
          f"{len(found)} of {len(store.items)} recalled")
    print(as_block(found))

# The customer asks for their contact details to be deleted.
store.forget(CUSTOMER, "contact")
left = [m.key for m in store.items]
print()
print(f"after forget: {len(left)} memories, "
      f"contact held: {'contact' in left}")
