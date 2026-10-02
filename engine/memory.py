"""memory.py -- facts that outlive one conversation."""
import json
import os
from dataclasses import asdict, dataclass
from datetime import date

from engine.retrieval import words


@dataclass
class Memory:
    subject: str         # who or what the fact is about
    key: str             # the slot it fills, e.g. "contact"
    text: str            # the fact, as a sentence
    source: str          # where it came from
    saved: str           # ISO date it was written
    used: str            # ISO date it was last recalled


class MemoryStore:
    """A JSON file of memories. One fact per subject and key."""

    def __init__(self, path: str):
        self.path = path
        self.items: list[Memory] = []
        if os.path.exists(path):
            with open(path) as handle:
                self.items = [Memory(**row)
                              for row in json.load(handle)]

    def save(self) -> None:
        with open(self.path, "w") as handle:
            json.dump([asdict(m) for m in self.items], handle,
                      indent=1)

    def remember(self, subject, key, text, source, today: date):
        """Write a fact. It replaces any older fact in that slot."""
        self.items = [m for m in self.items
                      if (m.subject, m.key) != (subject, key)]
        stamp = today.isoformat()
        memory = Memory(subject, key, text, source, stamp, stamp)
        self.items.append(memory)
        self.save()
        return memory

    def forget(self, subject, key) -> None:
        self.items = [m for m in self.items
                      if (m.subject, m.key) != (subject, key)]
        self.save()

    def recall(self, subject, query, today: date, k=3,
               max_age_days=365) -> list[Memory]:
        """Facts about one subject that bear on the query."""
        wanted = set(words(query))
        scored = []
        for memory in self.items:
            age = (today - date.fromisoformat(memory.saved)).days
            if memory.subject != subject or age > max_age_days:
                continue
            overlap = len(wanted & set(words(memory.text)))
            if overlap:
                scored.append((overlap, memory.saved, memory))
        scored.sort(key=lambda row: row[1], reverse=True)
        scored.sort(key=lambda row: row[0], reverse=True)
        chosen = [memory for _, _, memory in scored[:k]]
        for memory in chosen:
            memory.used = today.isoformat()
        self.save()
        return chosen


def as_block(memories: list[Memory]) -> str:
    return "\n".join(f"- {m.text} (noted {m.saved}, {m.source})"
                     for m in memories)
