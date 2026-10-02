"""ch13b_demo.py -- the suite catches a well-meant change."""
from engine.evals import Case, run_suite, table
from engine.selection import expand
from engine.tokens import get_counter
from support_agent import build_engine, route
from support_data import CUSTOMER, GLOSSARY

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


FULL = ("state", "memory", "tool result", "summary")
TRIMMED = ("memory", "tool result", "summary")


def builder(sources: tuple):
    """The engine's answer-step context, for given sources."""
    def build(request_text: str) -> str:
        engine = build_engine()
        engine.recipes["answer"].sources = sources
        if route(request_text) == "network":
            calls = [("check_outage", {"postal_code": "560001"})]
        else:
            query = expand(request_text, GLOSSARY)
            calls = [("lookup_account", {"customer_id": CUSTOMER}),
                     ("search_policies", {"query": query})]
        results = [(tool, str(engine.toolbox.call(tool, args)))
                   for tool, args in calls]
        request = engine.build("answer", request_text, results)
        return request["messages"][0]["content"]
    return build


for title, sources in (("before the change", FULL),
                       ("state removed from the answer step",
                        TRIMMED)):
    print(table(title, run_suite(CASES, builder(sources), counter)))
    print()
