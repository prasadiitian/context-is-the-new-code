"""ch13_demo.py -- the same test suite on two context builders."""
import json
import os

from engine.evals import Case, needle_test, position, run_suite, table
from engine.model import HttpModel
from engine.selection import expand
from engine.tokens import get_counter
from support_agent import build_engine, route
from support_data import (CUSTOMER, GLOSSARY, POLICIES,
                          billing_record, history)

counter = get_counter()

CASES = [
    Case("refund", "Can I cancel and get my money back?",
         must_include=["14 days", "Days since sign-up: 23",
                       "10 March 2026"],
         must_exclude=["30 days of sign-up"]),
    Case("outage", "My connection keeps dropping. Is there an "
                   "outage?",
         must_include=["No known outage", "fault logged"]),
    Case("contact", "How will you contact me about the repair?",
         must_include=["email"]),
    Case("plan change", "Can I move to a faster plan?",
         must_include=["faster plan at any time"],
         must_exclude=["30 days of sign-up"]),
]


def naive(request_text: str) -> str:
    """Everything, in the order it arrived. No selection at all."""
    parts = [f"{role}: {text}" for role, text in history()]
    parts += [p["text"] for p in POLICIES]
    parts.append(json.dumps(billing_record(CUSTOMER), indent=1))
    parts.append(request_text)
    return "\n".join(parts)


def engineered(request_text: str) -> str:
    """The engine's context at the answer step."""
    engine = build_engine()
    box = engine.toolbox
    if route(request_text) == "network":
        calls = [("check_outage", {"postal_code": "560001"})]
    else:
        query = expand(request_text, GLOSSARY)
        calls = [("lookup_account", {"customer_id": CUSTOMER}),
                 ("search_policies", {"query": query})]
    results = [(tool, str(box.call(tool, args)))
               for tool, args in calls]
    request = engine.build("answer", request_text, results)
    return request["messages"][0]["content"]


print(table("naive builder", run_suite(CASES, naive, counter)))
print()
print(table("engine", run_suite(CASES, engineered, counter)))

print()
print("where the refund rule sits:")
question = CASES[0].request
for name, build in (("naive", naive), ("engine", engineered)):
    print(f"  {name:8}{position(build(question), '14 days')}")

# The position test needs a real model, so it runs only with one.
if os.environ.get("MODEL_URL"):
    filler = [f"Note {n}: the office plant was watered."
              for n in range(200)]
    outcome = needle_test(
        HttpModel(), filler, "Note: the door code is 4172.",
        "What is the door code?", "4172")
    print()
    print("needle test (depth: found):", outcome)
