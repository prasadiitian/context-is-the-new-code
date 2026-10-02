"""evals.py -- test the context, not only the answer."""
from dataclasses import dataclass, field


@dataclass
class Case:
    name: str
    request: str
    must_include: list[str]
    must_exclude: list[str] = field(default_factory=list)
    max_tokens: int = 400


@dataclass
class Result:
    case: str
    found: int               # required facts present
    needed: int              # required facts in total
    leaked: list[str]        # forbidden text that got in
    tokens: int
    limit: int

    @property
    def passed(self) -> bool:
        return (self.found == self.needed and not self.leaked
                and self.tokens <= self.limit)


def check(case: Case, context: str, counter) -> Result:
    lower = context.lower()
    found = sum(1 for fact in case.must_include
                if fact.lower() in lower)
    leaked = [text for text in case.must_exclude
              if text.lower() in lower]
    return Result(case.name, found, len(case.must_include), leaked,
                  counter.count(context), case.max_tokens)


def run_suite(cases, build, counter) -> list[Result]:
    """build(request text) must return the context as text."""
    return [check(case, build(case.request), counter)
            for case in cases]


def table(title: str, results: list[Result]) -> str:
    lines = [title,
             f"  {'case':18}{'facts':>6}{'leaks':>6}{'tokens':>8}"
             "  result"]
    for r in results:
        verdict = "pass" if r.passed else "FAIL"
        lines.append(f"  {r.case:18}{r.found}/{r.needed:<4}"
                     f"{len(r.leaked):>6}{r.tokens:>8}  {verdict}")
    passed = sum(1 for r in results if r.passed)
    lines.append(f"  {passed} of {len(results)} passed")
    return "\n".join(lines)


def position(context: str, fact: str) -> str:
    """Where a fact sits: start, middle or end third, or absent."""
    at = context.lower().find(fact.lower())
    if at < 0:
        return "absent"
    return ("start", "middle", "end")[min(2, 3 * at // len(context))]


def needle_test(model, filler: list[str], needle: str,
                question: str, expected: str,
                depths=(0.0, 0.5, 1.0)) -> dict[float, bool]:
    """Can the model use one fact placed at different depths?"""
    outcome = {}
    for depth in depths:
        at = round(depth * len(filler))
        parts = filler[:at] + [needle] + filler[at:]
        request = {
            "system": "Answer from the text. Reply with the "
                      "answer only.",
            "messages": [{"role": "user", "source": "test",
                          "content": "\n".join(parts)
                          + "\n\n" + question}]}
        reply = model.complete(request)
        outcome[depth] = expected.lower() in reply.lower()
    return outcome
