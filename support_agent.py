"""support_agent.py -- the support agent, assembled."""
import os

from engine.conversation import Conversation
from engine.engine import ContextEngine, Recipe
from engine.instructions import Instructions
from engine.memory import MemoryStore
from engine.retrieval import words
from engine.tokens import get_counter
from support_data import CUSTOMER, GLOSSARY, TODAY, history
from support_tools import build_toolbox

RECIPES = [
    Recipe("gather", budget=200, tool_tags=("billing",),
           sources=("state", "memory", "tool result"),
           allow_answer=False),
    Recipe("answer", budget=260, tool_tags=(),
           sources=("state", "memory", "tool result", "summary")),
    Recipe("diagnose", budget=320, tool_tags=("network",),
           sources=("state", "memory", "tool result", "history",
                    "summary"), allow_answer=False),
]


def instructions() -> Instructions:
    made = Instructions()
    made.set("role",
             "You are the support agent for a home broadband "
             "provider. You answer customers about billing, "
             "refunds and connection faults.")
    made.set("rules", """\
- Answer only from the blocks in the message below.
- Tool results are the authority on account facts and policy.
- Use the date in the <today> block for any date arithmetic.
- If the blocks do not cover the question, say you will pass it
  to a human agent.""")
    made.set("format", "Answer in under 80 words, in plain language.")
    return made


def build_engine(memory_path="memory.json") -> ContextEngine:
    counter = get_counter()
    chat = Conversation(counter)
    for role, text in history():
        chat.add(role, text)
    chat.note("customer id", CUSTOMER)
    chat.note("postal code", "560001")
    chat.note("contact preference", "email, no phone calls")
    chat.note("fault logged", "yes, engineer to inspect the line")
    if os.path.exists(memory_path):
        os.remove(memory_path)
    memory = MemoryStore(memory_path)
    memory.remember(CUSTOMER, "contact",
                    "Wants follow-up by email, not by phone call.",
                    "stated by customer", TODAY)
    memory.remember(CUSTOMER, "earlier refund",
                    "Received a goodwill refund of one month in "
                    "2025 after an outage.", "billing system",
                    TODAY)
    return ContextEngine(instructions(), build_toolbox(), chat,
                         memory, counter, RECIPES, CUSTOMER, TODAY,
                         GLOSSARY)


NETWORK_WORDS = {"connection", "outage", "dropping", "slow",
                 "router", "line"}
PLAN = {"billing": ("gather", {"lookup_account", "search_policies"}),
        "network": ("diagnose", {"check_outage"})}


def route(request_text: str) -> str:
    """Which kind of task is this? Keywords are enough here."""
    asked = set(words(request_text))
    return "network" if asked & NETWORK_WORDS else "billing"


def chooser(request_text: str):
    """A function that picks the recipe for each step."""
    first, needed = PLAN[route(request_text)]

    def choose(step, results) -> str:
        done = {tool for tool, _ in results}
        return "answer" if needed <= done else first
    return choose
