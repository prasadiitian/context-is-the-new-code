"""assembler.py -- fit labelled context items into a budget."""
from dataclasses import dataclass, field

from engine.tokens import get_counter


@dataclass
class ContextItem:
    source: str          # which of the six sources it came from
    content: str         # the text the model will read
    priority: int = 2    # 1 = must keep; larger is dropped first
    meta: dict = field(default_factory=dict)
    tokens: int = 0


def render(item: ContextItem) -> str:
    return f"<{item.source}>\n{item.content}\n</{item.source}>"


class ContextAssembler:
    """Collects context items and fits them into a token budget."""

    def __init__(self, budget: int, counter=None):
        self.budget = budget
        self.counter = counter or get_counter()
        self.items: list[ContextItem] = []
        self.dropped: list[ContextItem] = []

    def add(self, source, content, priority=2, **meta):
        item = ContextItem(source, content, priority, meta)
        item.tokens = self.counter.count(content)
        self.items.append(item)
        return item

    def fit(self) -> list[ContextItem]:
        """The most important items that fit, in added order."""
        self.dropped = []
        keep, used = set(), 0
        order = sorted(range(len(self.items)),
                       key=lambda i: self.items[i].priority)
        for i in order:
            item = self.items[i]
            if used + item.tokens <= self.budget:
                keep.add(i)
                used += item.tokens
            else:
                self.dropped.append(item)
        return [it for i, it in enumerate(self.items) if i in keep]

    def build(self) -> str:
        return "\n\n".join(render(item) for item in self.fit())

    def report(self) -> str:
        gone = {id(item) for item in self.dropped}
        used = sum(it.tokens for it in self.items
                   if id(it) not in gone)
        lines = [f"budget {self.budget} tokens, used {used}"]
        for it in self.items:
            status = "DROPPED" if id(it) in gone else "kept"
            lines.append(
                f"  {status:8}{it.source:14}{it.tokens:5} tokens")
        return "\n".join(lines)
