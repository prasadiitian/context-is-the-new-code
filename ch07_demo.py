"""ch07_demo.py -- memory across two sessions."""
import os
from datetime import date

from engine.memory import MemoryStore, as_block
from engine.tokens import get_counter
from support_data import CUSTOMER

PATH = "memory.json"
if os.path.exists(PATH):
    os.remove(PATH)
counter = get_counter()

# Session 1, 10 March: the application saves what will matter later.
day1 = date(2026, 3, 10)
store = MemoryStore(PATH)
store.remember(CUSTOMER, "contact",
               "Wants follow-up by email, not by phone call.",
               "stated by customer", day1)
store.remember(CUSTOMER, "open fault",
               "Line fault logged; engineer to inspect the line.",
               "fault system", day1)
store.remember(CUSTOMER, "refund",
               "Asked for a refund at 23 days; outside the 14-day "
               "refund window.", "account lookup and policy", day1)
print(f"session 1 saved {len(store.items)} memories")

# Session 2, eight days later: a new process, a new conversation.
day2 = date(2026, 3, 18)
store = MemoryStore(PATH)
question = "Has the engineer fixed the fault on my line yet?"
found = store.recall(CUSTOMER, question, day2)
print()
print(f"session 2 question: {question}")
print(f"recalled {len(found)} of {len(store.items)} memories, "
      f"{counter.count(as_block(found))} tokens")
print(as_block(found))

# A fact changes: the new value replaces the old one.
store.remember(CUSTOMER, "open fault",
               "Engineer replaced the line on 17 March; fault "
               "closed.", "fault system", day2)
found = store.recall(CUSTOMER, question, day2)
print()
print("after the fault system reports the repair:")
print(as_block(found))

# Another customer never sees these.
other = store.recall("K-99999", question, day2)
print()
print(f"recalled for another customer: {len(other)}")

# Old memories expire from recall.
later = date(2027, 6, 1)
print(f"recalled in June 2027: "
      f"{len(store.recall(CUSTOMER, question, later))}")
