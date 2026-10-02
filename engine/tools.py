"""tools.py -- tool definitions, tool results and MCP listings."""
import json
from dataclasses import dataclass
from typing import Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict             # JSON Schema for the arguments
    run: Callable[..., object]
    tags: tuple = ()

    def definition(self) -> dict:
        return {"name": self.name, "description": self.description,
                "parameters": self.parameters}


def params(**args: str) -> dict:
    """A JSON Schema for string arguments: name -> description."""
    return {"type": "object",
            "properties": {name: {"type": "string",
                                  "description": text}
                           for name, text in args.items()},
            "required": list(args)}


class Toolbox:
    def __init__(self):
        self.tools: dict[str, Tool] = {}

    def add(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def select(self, *tags: str) -> list[Tool]:
        """Only the tools relevant to the current kind of task."""
        return [tool for tool in self.tools.values()
                if set(tags) & set(tool.tags)]

    def call(self, name: str, args: dict):
        """Run a tool. Failures come back as text, not exceptions."""
        if name not in self.tools:
            known = ", ".join(sorted(self.tools))
            return f"ERROR: no tool named '{name}'. Tools: {known}."
        try:
            return self.tools[name].run(**args)
        except Exception as error:
            return (f"ERROR: {name} failed "
                    f"({type(error).__name__}: {error}).")


def render_tools(tools: list[Tool], allow_answer=True) -> str:
    """Tool definitions and the reply convention, as text."""
    lines = ["These tools are available. Each is described as JSON:"]
    for tool in tools:
        lines.append(json.dumps(tool.definition()))
    lines.append('To use one, write only this JSON as your reply: '
                 '{"tool": "<name>", "args": {...}}')
    lines.append("Write it as ordinary text. Do not use a function "
                 "call.")
    if allow_answer:
        lines.append('To answer, write only this JSON: '
                     '{"answer": "<text>"}')
    else:
        lines.append("Do not answer yet. Use a tool you have not "
                     "used so far.")
    return "\n".join(lines)


def parse_reply(text: str) -> dict:
    """A model reply as {"tool", "args"} or {"answer"}."""
    start, end = text.find("{"), text.rfind("}")
    try:
        reply = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"answer": text}
    if isinstance(reply, dict) and ("tool" in reply
                                    or "answer" in reply):
        return reply
    return {"answer": text}


def shape(record: dict, fields: dict[str, str]) -> str:
    """Keep only the named fields, under readable labels."""
    return "\n".join(f"{label}: {record[key]}"
                     for key, label in fields.items()
                     if record.get(key) is not None)


def clip(text: str, limit: int, counter) -> str:
    """Cut an oversized result and say how much was removed."""
    total = counter.count(text)
    if total <= limit:
        return text
    kept = text[:limit * 4]
    return (f"{kept}\n[clipped: showing about {limit} of {total} "
            "tokens. Ask for a narrower result.]")


def from_mcp(listing: dict, run: Callable, tags=()) -> list[Tool]:
    """Tools from an MCP server's tools/list result."""
    tools = []
    for entry in listing["tools"]:
        name = entry["name"]
        tools.append(Tool(
            name, entry.get("description", ""),
            entry["inputSchema"],
            lambda _name=name, **args: run(_name, args), tags))
    return tools


def mcp_text(result: dict) -> str:
    """The text of an MCP tools/call result."""
    text = "\n".join(part["text"] for part in result["content"]
                     if part.get("type") == "text")
    return f"ERROR: {text}" if result.get("isError") else text
