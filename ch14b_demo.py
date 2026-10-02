"""ch14b_demo.py -- test a brief the way you test a context."""
from engine.conversation import Conversation, as_text
from engine.evals import Case, check, table
from engine.handoff import Brief
from engine.tokens import get_counter
from support_data import CUSTOMER, history
from support_tools import lookup_account, search_policies

counter = get_counter()
account = lookup_account(CUSTOMER).splitlines()
policy = search_policies("refund cancel").splitlines()
GOAL = "Decide whether this account qualifies for a refund."

good = Brief(goal=GOAL,
             known=["Today is 10 March 2026."] + account + policy,
             constraints=["Decide from these facts only."])
no_policy = Brief(goal=GOAL,
                  known=["Today is 10 March 2026."] + account)

chat = Conversation(counter)
for role, text in history():
    chat.add(role, text)
everything = "\n".join([as_text(chat.turns)] + account + policy)

NEEDS = Case("billing handoff", GOAL,
             must_include=["10 March 2026", "Days since sign-up",
                           "14 days"],
             must_exclude=["router"], max_tokens=200)

results = []
for name, text in (("full brief", good.render()),
                   ("policy left out", no_policy.render()),
                   ("whole transcript", everything)):
    result = check(NEEDS, text, counter)
    result.case = name
    results.append(result)
print(table("what the billing specialist receives", results))
