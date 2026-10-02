"""support_tools.py -- the support agent's tools."""
from datetime import date

from engine.retrieval import (Index, as_context, dedupe, in_force,
                              split)
from engine.tools import Tool, Toolbox, params, shape
from support_data import POLICIES, TODAY, billing_record

ACCOUNT_FIELDS = {"plan": "Plan", "signup_date": "Signed up",
                  "contact_channel": "Contact channel on file"}


def build_index() -> Index:
    index = Index()
    for policy in POLICIES:
        meta = {"title": policy["title"],
                "effective": policy["effective"],
                "superseded": policy["superseded"]}
        for chunk in split(policy["id"], policy["text"], meta):
            index.add(chunk)
    return index


INDEX = build_index()


def search_policies(query: str) -> str:
    hits = INDEX.search(query, k=5, where=in_force(TODAY))
    if not hits:
        return "No policy matches that query."
    strong = [hit for hit in hits if hit[0] >= 0.5 * hits[0][0]]
    return as_context(dedupe(strong))


def lookup_account(customer_id: str) -> str:
    record = billing_record(customer_id)
    signed_up = date.fromisoformat(record["signup_date"])
    days = (TODAY - signed_up).days
    return (shape(record, ACCOUNT_FIELDS)
            + f"\nDays since sign-up: {days}")


def check_outage(postal_code: str) -> str:
    if not postal_code.isdigit():
        raise ValueError("postal code must be digits only")
    return f"No known outage for postal code {postal_code}."


def reset_line(customer_id: str) -> str:
    return f"Line reset sent for {customer_id}. Allow two minutes."


def build_toolbox() -> Toolbox:
    box = Toolbox()
    box.add(Tool("lookup_account",
                 "Fetch plan and sign-up facts for one customer.",
                 params(customer_id="The account identifier."),
                 lookup_account, tags=("billing",)))
    box.add(Tool("search_policies",
                 "Search policies in force today; returns excerpts.",
                 params(query="What to look for, in plain words."),
                 search_policies, tags=("billing", "network")))
    box.add(Tool("check_outage",
                 "Report known network outages for a postal code.",
                 params(postal_code="Digits only."),
                 check_outage, tags=("network",)))
    box.add(Tool("reset_line",
                 "Send a remote reset to the customer's line.",
                 params(customer_id="The account identifier."),
                 reset_line, tags=("network",)))
    return box
