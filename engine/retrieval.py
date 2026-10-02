"""retrieval.py -- a small, exact, dependency-free retriever."""
import math
import re
from dataclasses import dataclass, field

STOP = {"a", "an", "and", "are", "can", "for", "get", "i", "is",
        "it", "my", "of", "the", "to", "we", "you", "your"}


def words(text: str) -> list[str]:
    found = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in found if w not in STOP]


@dataclass
class Chunk:
    doc_id: str
    text: str
    meta: dict = field(default_factory=dict)


def split(doc_id, text, meta, max_words=120) -> list[Chunk]:
    """Split on blank lines, then pack paragraphs into chunks."""
    chunks, current = [], []
    for para in text.split("\n\n"):
        size = sum(len(p.split()) for p in current)
        if current and size + len(para.split()) > max_words:
            chunks.append(Chunk(doc_id, "\n\n".join(current), meta))
            current = []
        current.append(para.strip())
    chunks.append(Chunk(doc_id, "\n\n".join(current), meta))
    return chunks


class Index:
    """BM25 ranking over chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.chunks: list[Chunk] = []
        self.terms: list[list[str]] = []

    def add(self, chunk: Chunk) -> None:
        self.chunks.append(chunk)
        self.terms.append(words(chunk.text))

    def search(self, query, k=5, where=None):
        """Top k (score, chunk) pairs, best first."""
        n = len(self.chunks)
        average = sum(len(t) for t in self.terms) / n
        scored = []
        for chunk, terms in zip(self.chunks, self.terms):
            if where and not where(chunk.meta):
                continue
            score = 0.0
            for word in set(words(query)):
                tf = terms.count(word)
                if tf == 0:
                    continue
                df = sum(1 for t in self.terms if word in t)
                idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
                norm = 1 - self.b + self.b * len(terms) / average
                score += idf * tf * (self.k1 + 1) / (
                    tf + self.k1 * norm)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: -pair[0])
        return scored[:k]


def in_force(today):
    """A filter that keeps only documents valid on a given day."""
    def check(meta):
        ended = meta.get("superseded")
        return meta["effective"] <= today and (
            ended is None or today < ended)
    return check


def similar(a: str, b: str) -> float:
    """Share of words two texts have in common (0 to 1)."""
    x, y = set(words(a)), set(words(b))
    return len(x & y) / len(x | y) if x | y else 0.0


def numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def repeats(a: str, b: str, threshold: float = 0.6) -> bool:
    """True when b says what a says: like words, same numbers."""
    return (similar(a, b) >= threshold
            and numbers(a) == numbers(b))


def dedupe(hits, threshold=0.6):
    """Drop hits that repeat a higher-ranked one."""
    kept = []
    for score, chunk in hits:
        if not any(repeats(other.text, chunk.text, threshold)
                   for _, other in kept):
            kept.append((score, chunk))
    return kept


def as_context(hits) -> str:
    """Each hit with a header saying what it is and from when."""
    blocks = []
    for _, chunk in hits:
        meta = chunk.meta
        head = (f"[{meta['title']} | {chunk.doc_id} | "
                f"in force from {meta['effective']}]")
        blocks.append(f"{head}\n{chunk.text}")
    return "\n\n".join(blocks)
