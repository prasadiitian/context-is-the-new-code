"""handoff.py -- pass work between agents without the baggage."""
from dataclasses import dataclass, field


def block(tag: str, lines: list[str]) -> str:
    body = "\n".join(f"- {line}" for line in lines)
    return f"<{tag}>\n{body}\n</{tag}>"


@dataclass
class Brief:
    """Everything a worker needs for one job, and nothing else."""
    goal: str
    known: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    reply_format: str = "Reply in at most three short lines."

    def render(self) -> str:
        parts = [f"<goal>\n{self.goal}\n</goal>"]
        if self.known:
            parts.append(block("known", self.known))
        if self.constraints:
            parts.append(block("constraints", self.constraints))
        parts.append(f"<reply>\n{self.reply_format}\n</reply>")
        return "\n\n".join(parts)


class Ledger:
    """Input tokens spent by each agent."""

    def __init__(self, counter):
        self.counter = counter
        self.spent: dict[str, int] = {}

    def charge(self, agent: str, request: dict) -> int:
        tokens = self.counter.count(request["system"]) + sum(
            self.counter.count(msg["content"])
            for msg in request["messages"])
        self.spent[agent] = self.spent.get(agent, 0) + tokens
        return tokens

    def total(self) -> int:
        return sum(self.spent.values())


@dataclass
class Worker:
    name: str
    role: str                # the worker's own system instructions
    model: object

    def work(self, content: str, ledger: Ledger) -> str:
        """One call: the worker sees its role and this content."""
        request = {"system": self.role, "messages": [
            {"role": "user", "source": "brief", "content": content}]}
        ledger.charge(self.name, request)
        reply = " ".join(self.model.complete(request).split())
        return f"[from {self.name}] {reply}"
