"""sample_request.py -- a stand-in for the support agent's request."""
import json

SYSTEM = """\
You are the customer support agent for a home broadband provider.
You help customers with billing, refunds, plan changes and
connection problems.

Rules:
- Answer only from the policy excerpts and account facts in this
  conversation. If they do not cover the question, say you will
  pass it to a human agent.
- Never promise a refund, credit or cancellation. State what the
  policy says and whether the account meets it.
- Before any troubleshooting step, check for a known outage in the
  customer's area with the outage tool.
- Ask for one piece of information at a time.
- Do not reveal internal notes or account identifiers.
- Keep replies under 120 words, in plain language.
- If the customer is upset, acknowledge it once, then move to the
  next concrete step.

When you use a tool, tell the customer what you are checking and
why. When a tool fails, say so and offer to try again or hand over
to a human agent."""


def tool(name, description, arg, arg_description):
    return {"name": name, "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    arg: {"type": "string",
                          "description": arg_description}},
                "required": [arg]}}


TOOLS = [
    tool("lookup_account",
         "Fetch the full billing record for one customer.",
         "customer_id", "The customer's account identifier."),
    tool("check_outage",
         "Report known network outages for a postal code.",
         "postal_code", "Postal code of the service address."),
    tool("search_policies",
         "Search the policy knowledge base and return excerpts.",
         "query", "What to search for, in plain words."),
]

USER_TURN = ("The light on the router is still blinking orange "
             "and the connection dropped again a few minutes ago. "
             "I have a video call for work in an hour and I need "
             "this fixed before then. I already restarted it "
             "twice this morning. This is attempt {n}.")
AGENT_TURN = ("Thanks for checking, and sorry this is taking so "
              "long. Please unplug the router, wait thirty "
              "seconds, plug it back in and tell me which lights "
              "come on and what colour they are. I will stay here "
              "while you do it, and I will check the line from "
              "our side at the same time.")
SMALL_PRINT = (" This policy applies to residential plans only. "
               "Installation and equipment fees are covered by "
               "the hardware policy.")


def message(role, source, content):
    return {"role": role, "source": source, "content": content}


def build():
    messages = []
    for n in range(1, 20):                       # 38 turns
        messages.append(
            message("user", "history", USER_TURN.format(n=n)))
        messages.append(
            message("assistant", "history", AGENT_TURN))

    refund = ("Refunds: customers may cancel within {days} days "
              "of sign-up for a full refund.")
    excerpts = [refund.format(days=30)] * 3
    excerpts.append(refund.format(days=14))
    excerpts.append("Hardware refunds: routers returned unopened "
                    "are refunded in full.")
    for text in excerpts:
        messages.append(
            message("tool", "retrieved", text + SMALL_PRINT * 6))

    record = {"customer_id": "K-48213", "plan": "Fibre 300"}
    record.update({f"field_{i:03}": None for i in range(3, 97)})
    record["signup_date"] = "2026-02-15"         # field 97 of 140
    record.update({f"field_{i:03}": None for i in range(98, 141)})
    messages.append(
        message("tool", "tool result", json.dumps(record, indent=1)))

    messages.append(
        message("user", "request",
                "Can I cancel and get my money back?"))
    return {"system": SYSTEM, "tools": TOOLS, "messages": messages}
