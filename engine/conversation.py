"""conversation.py -- conversation state and short-term memory."""
from dataclasses import dataclass

from engine.tokens import get_counter


@dataclass
class Turn:
    role: str            # "user" or "assistant"
    content: str
    tokens: int = 0


class Conversation:
    """Every turn of one session, plus the facts settled so far."""

    def __init__(self, counter=None):
        self.counter = counter or get_counter()
        self.turns: list[Turn] = []
        self.facts: dict[str, str] = {}
        self.summary = ""            # filled in by Chapter 9

    def add(self, role: str, content: str) -> Turn:
        turn = Turn(role, content, self.counter.count(content))
        self.turns.append(turn)
        return turn

    def note(self, key: str, value: str) -> None:
        """Record a settled fact. A new value replaces the old."""
        self.facts[key] = value

    def total_tokens(self) -> int:
        return sum(turn.tokens for turn in self.turns)

    def recent(self, budget: int) -> list[Turn]:
        """The newest turns that fit, starting on a user turn."""
        kept, used = [], 0
        for turn in reversed(self.turns):
            if used + turn.tokens > budget:
                break
            kept.append(turn)
            used += turn.tokens
        kept.reverse()
        while kept and kept[0].role != "user":
            kept.pop(0)
        return kept

    def state_block(self) -> str:
        """Settled facts as text for the context."""
        return "\n".join(f"- {key}: {value}"
                         for key, value in self.facts.items())


def as_text(turns: list[Turn]) -> str:
    label = {"user": "Customer", "assistant": "Agent"}
    return "\n".join(f"{label[t.role]}: {t.content}" for t in turns)
