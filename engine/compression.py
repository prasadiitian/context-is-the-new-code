"""compression.py -- say the same thing in fewer tokens."""
import re

from engine.conversation import Conversation, as_text
from engine.retrieval import repeats, words


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if part.strip()]


def extract(text: str, query: str, keep: int = 2) -> str:
    """The sentences that best match the query, in their order."""
    parts = sentences(text)
    wanted = set(words(query))
    ranked = sorted(
        range(len(parts)),
        key=lambda i: -len(wanted & set(words(parts[i]))))
    return " ".join(parts[i] for i in sorted(ranked[:keep]))


def squeeze(texts: list[str], threshold: float = 0.6) -> list[str]:
    """Drop texts that repeat an earlier one."""
    kept: list[str] = []
    for text in texts:
        if not any(repeats(other, text, threshold)
                   for other in kept):
            kept.append(text)
    return kept


def head_tail(text: str, limit: int, counter) -> str:
    """Keep the start and the end; mark what was cut between."""
    total = counter.count(text)
    if total <= limit:
        return text
    half = limit * 2                 # characters for each end
    cut = total - limit
    return (f"{text[:half]}\n[... about {cut} tokens cut ...]\n"
            f"{text[-half:]}")


SUMMARY_PROMPT = """\
Summarise the conversation below for a support agent who will
continue it. Keep every fact about the customer, the account and
the fault, every commitment that was made, and anything still
unresolved. Leave out greetings and repeated steps. Use short
bullet points and at most {max_words} words."""


def summarise(text: str, model, max_words: int = 80) -> str:
    """Ask a model for a summary. The one lossy step that costs."""
    request = {
        "system": SUMMARY_PROMPT.format(max_words=max_words),
        "messages": [{"role": "user", "source": "history",
                      "content": text}]}
    return model.complete(request).strip()


def compact(chat: Conversation, model, keep_tokens: int) -> int:
    """Fold turns older than the recent window into a summary."""
    recent = chat.recent(keep_tokens)
    old = chat.turns[:len(chat.turns) - len(recent)]
    if not old:
        return 0
    text = as_text(old)
    if chat.summary:
        text = f"Summary so far:\n{chat.summary}\n\n{text}"
    chat.summary = summarise(text, model)
    chat.turns = recent
    return len(old)


def lost(summary: str, must_keep: list[str]) -> list[str]:
    """Facts the summary was required to keep and did not.

    A fact is kept when all of its words appear, in any order.
    It may list accepted wordings: "three weeks|3 weeks".
    """
    present = set(words(summary))
    return [fact for fact in must_keep
            if not any(set(words(form)) <= present
                       for form in fact.split("|"))]
