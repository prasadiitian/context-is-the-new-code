"""trace.py -- a record of every context the engine built."""
import json


class Tracer:
    """Appends one JSON line per context to a file."""

    def __init__(self, path: str):
        self.path = path
        open(path, "w").close()          # start a fresh trace

    def log(self, record: dict) -> None:
        with open(self.path, "a") as handle:
            handle.write(json.dumps(record) + "\n")


def read(path: str) -> list[dict]:
    with open(path) as handle:
        return [json.loads(line) for line in handle if line.strip()]


def input_tokens(record: dict) -> int:
    return record["system"] + sum(record["body"].values())


def summary(records: list[dict]) -> str:
    lines = []
    for r in records:
        lines.append(
            f"step {r['step']}  {r['recipe']:8} version "
            f"{r['version']}  {input_tokens(r):4} tokens in")
        for flag in r["flags"]:
            lines.append(f"    FLAG {flag}")
    total = sum(input_tokens(r) for r in records)
    lines.append(f"{len(records)} steps, {total} input tokens")
    return "\n".join(lines)
