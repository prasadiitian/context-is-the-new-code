"""ch14_demo.py -- one request, three agents, two designs."""
import json

from engine.conversation import Conversation, as_text
from engine.handoff import Brief, Ledger, Worker
from engine.model import ScriptedModel
from engine.tokens import get_counter
from support_data import CUSTOMER, billing_record, history
from support_tools import (check_outage, lookup_account,
                           search_policies)

counter = get_counter()
REQUEST = ("My connection keeps dropping and I want my money back "
           "for this month.")

BILLING = ("You are the billing specialist. Decide refund "
           "questions from the facts given. Do not discuss faults.")
NETWORK = ("You are the network specialist. Assess connection "
           "faults from the facts given. Do not discuss billing.")
LEAD = ("You are the lead support agent. Write one reply to the "
        "customer from the specialists' findings.")

BILLING_REPLY = ("Not eligible for a refund: signed up 23 days "
                 "ago and the window is 14 days (refund-2026).\n"
                 "The customer may still cancel.")
NETWORK_REPLY = ("No known outage for 560001.\n"
                 "A fault is logged; an engineer will inspect the "
                 "line.")
LEAD_REPLY = ("There is no outage in your area, and an engineer "
              "will inspect your line. I cannot refund this month "
              "because the account is past the 14-day window. I "
              "will follow up by email.")


def team():
    def make(name, role, reply):
        return Worker(name, role, ScriptedModel([reply]))
    return (make("billing", BILLING, BILLING_REPLY),
            make("network", NETWORK, NETWORK_REPLY),
            make("lead", LEAD, LEAD_REPLY))


chat = Conversation(counter)
for role, text in history():
    chat.add(role, text)
account = lookup_account(CUSTOMER)
policy = search_policies("refund cancel")
outage = check_outage("560001")

# Design A: every agent receives everything.
shared = "\n\n".join([
    as_text(chat.turns), json.dumps(billing_record(CUSTOMER)),
    policy, outage, f"Customer: {REQUEST}"])
ledger_a = Ledger(counter)
billing, network, lead = team()
found = [billing.work(shared, ledger_a),
         network.work(shared, ledger_a)]
lead.work(shared + "\n\n" + "\n\n".join(found), ledger_a)

# Design B: each agent receives a brief written for its job.
ledger_b = Ledger(counter)
billing, network, lead = team()
billing_brief = Brief(
    goal="Decide whether this account qualifies for a refund.",
    known=["Today is 10 March 2026."] + account.splitlines()
          + policy.splitlines(),
    constraints=["Decide from these facts only."])
network_brief = Brief(
    goal="Assess the connection fault and name the next step.",
    known=[outage, "Fault logged; engineer to inspect the line.",
           "Line test showed a weak signal.",
           "Router restarted three times."])
found = [billing.work(billing_brief.render(), ledger_b),
         network.work(network_brief.render(), ledger_b)]
lead_brief = Brief(
    goal="Write one reply to the customer covering both issues.",
    known=[f"The customer wrote: {REQUEST}",
           "Contact preference: email, no phone calls."] + found,
    reply_format="Under 80 words, plain language.")
answer = lead.work(lead_brief.render(), ledger_b)

print(f"{'agent':10}{'everything':>12}{'briefs':>9}")
for name in ("billing", "network", "lead"):
    print(f"{name:10}{ledger_a.spent[name]:12,}"
          f"{ledger_b.spent[name]:9,}")
print(f"{'total':10}{ledger_a.total():12,}{ledger_b.total():9,}")

print()
print("--- the billing specialist's brief ---")
print(billing_brief.render())
print()
print("--- the lead agent's brief ---")
print(lead_brief.render())
print()
print(answer)
