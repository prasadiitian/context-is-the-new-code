"""tokens.py -- count tokens with whatever is available."""


class HeuristicCounter:
    """About four characters per token. Rough, no dependencies."""
    name = "heuristic (4 characters per token)"

    def count(self, text: str) -> int:
        return max(1, len(text) // 4)


class TiktokenCounter:
    """Exact counts for models that use an OpenAI tokenizer."""
    name = "tiktoken"

    def __init__(self, encoding: str = "o200k_base"):
        import tiktoken
        self.enc = tiktoken.get_encoding(encoding)

    def count(self, text: str) -> int:
        return len(self.enc.encode(text))


def get_counter():
    """Use a real tokenizer when one is installed and usable."""
    try:
        return TiktokenCounter()
    except Exception:
        return HeuristicCounter()
