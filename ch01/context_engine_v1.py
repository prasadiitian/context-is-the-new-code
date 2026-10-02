"""context_engine_v1.py -- Chapter 1: a minimal assembler."""
from dataclasses import dataclass, field
from datetime import date


def estimate_tokens(text: str) -> int:
    """Rough estimate: about four characters per token."""
    return max(1, len(text) // 4)


@dataclass
class ContextItem:
    source: str      # where it came from: "instructions", ...
    content: str     # the text the model will read
    priority: int    # 1 = must keep; larger is dropped first
    tokens: int = field(init=False)

    def __post_init__(self):
        self.tokens = estimate_tokens(self.content)


class ContextAssembler:
    """Collects context items and fits them into a token budget."""

    def __init__(self, budget: int):
        self.budget = budget
        self.items: list[ContextItem] = []
        self.dropped: list[ContextItem] = []

    def add(self, source: str, content: str, priority: int) -> None:
        self.items.append(ContextItem(source, content, priority))

    def build(self) -> str:
        """Keep the most important items that fit, in added order."""
        self.dropped = []
        keep, used = set(), 0
        ranked = sorted(range(len(self.items)),
                        key=lambda i: self.items[i].priority)
        for i in ranked:
            item = self.items[i]
            if used + item.tokens <= self.budget:
                keep.add(i)
                used += item.tokens
            else:
                self.dropped.append(item)
        parts = [f"<{it.source}>\n{it.content}\n</{it.source}>"
                 for i, it in enumerate(self.items) if i in keep]
        return "\n\n".join(parts)

    def report(self) -> str:
        used = sum(it.tokens for it in self.items
                   if it not in self.dropped)
        lines = [f"budget {self.budget} tokens, used {used}"]
        for it in self.items:
            status = "DROPPED" if it in self.dropped else "kept"
            lines.append(
                f"  {status:8}{it.source:14}{it.tokens:5} tokens")
        return "\n".join(lines)


# --- The support agent's data on the customer's final turn -------

TODAY = date(2026, 3, 10)

policies = [
    {"text": "Refunds: customers may cancel within 30 days of "
             "sign-up for a full refund.",
     "effective": date(2024, 1, 1), "superseded": date(2026, 1, 1)},
    {"text": "Refunds: customers may cancel within 14 days of "
             "sign-up for a full refund.",
     "effective": date(2026, 1, 1), "superseded": None},
]

billing_record = {"customer_id": "K-48213", "plan": "Fibre 300",
                  "signup_date": date(2026, 2, 15),
                  "router_model": "KX-2",
                  "autopay": True}          # ...and 135 more fields

history = "\n".join(
    f"turn {n}: (router troubleshooting, restart steps, light status)"
    for n in range(1, 39))

request = "Can I cancel and get my money back?"


# --- Fix 1: only policies in force today --------------------------

def current_policies(docs, today):
    return [d["text"] for d in docs
            if d["effective"] <= today
            and (d["superseded"] is None or today < d["superseded"])]


# --- Fix 2: turn the raw record into the facts this task needs ----

def account_facts(record, today):
    days = (today - record["signup_date"]).days
    return (f"Plan: {record['plan']}. "
            f"Signed up {record['signup_date']:%d %B %Y}, "
            f"{days} days ago.")


# --- Assemble ------------------------------------------------------

ctx = ContextAssembler(budget=300)
ctx.add("instructions",
        "You are the support agent for a broadband provider. "
        "Answer from the policy and account facts provided. If "
        "they do not cover the question, say so.", priority=1)
ctx.add("today", f"Today is {TODAY:%d %B %Y}.", priority=1)
ctx.add("policy", "\n".join(current_policies(policies, TODAY)),
        priority=1)
ctx.add("account", account_facts(billing_record, TODAY), priority=1)
ctx.add("history", history, priority=3)
ctx.add("request", request, priority=1)

if __name__ == "__main__":
    print(ctx.build())
    print()
    print(ctx.report())
