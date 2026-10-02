"""instructions.py -- system instructions as structured data."""
import hashlib
import re
from dataclasses import dataclass, field

ORDER = ["role", "rules", "format", "escalation"]


@dataclass
class Instructions:
    sections: dict[str, str] = field(default_factory=dict)

    def set(self, name: str, text: str) -> "Instructions":
        self.sections[name] = text.strip()
        return self

    def render(self, **values) -> str:
        """Sections in a fixed order, with {placeholders} filled."""
        extra = sorted(set(self.sections) - set(ORDER))
        parts = []
        for name in ORDER + extra:
            if name in self.sections:
                body = self.sections[name].format(**values)
                parts.append(f"## {name.title()}\n{body}")
        return "\n\n".join(parts)

    def version(self) -> str:
        """A short fingerprint that changes when any word changes."""
        raw = "\n".join(f"{name}={text}" for name, text
                        in sorted(self.sections.items()))
        return hashlib.sha256(raw.encode()).hexdigest()[:8]


UNANCHORED = ["current", "latest", "up to date", "recent"]
GOALS = ["never give wrong", "be accurate", "do not hallucinate",
         "always be correct"]
CLASHES = [("concise", "thorough"), ("brief", "detailed")]


def lint(instructions: Instructions) -> list[str]:
    """Warnings about instructions a model cannot act on."""
    text = " ".join(instructions.sections.values())
    lower = text.lower()
    warnings = []
    shouted = re.findall(r"\b[A-Z]{4,}\b", text)
    if len(shouted) >= 3:
        warnings.append(
            f"{len(shouted)} words in capitals: emphasis adds no "
            "information")
    for word in UNANCHORED:
        if word in lower:
            warnings.append(
                f"'{word}' is not anchored: say where in the "
                "context the model finds it")
    for goal in GOALS:
        if goal in lower:
            warnings.append(
                f"'{goal}' states a goal, not an action")
    for a, b in CLASHES:
        if a in lower and b in lower:
            warnings.append(f"asks for both '{a}' and '{b}'")
    if "helpful assistant" in lower:
        warnings.append("role is generic: name the job and the user")
    return warnings
