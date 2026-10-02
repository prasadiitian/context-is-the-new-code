"""engine.py -- build the right context for each step."""
from dataclasses import dataclass, field

from engine.assembler import ContextItem, render
from engine.caching import order_for_cache
from engine.conversation import as_text
from engine.memory import as_block
from engine.model import ModelError
from engine.selection import expand, select
from engine.tools import parse_reply, render_tools

UNREADABLE = ("The last reply could not be read. Reply with the "
              "JSON as ordinary text and nothing else.")
TOO_EARLY = ("An answer was given before the facts were gathered. "
             "Call a tool that has not been called yet.")
ANSWER_ONLY = ('Write only this JSON as your reply, as ordinary '
               'text: {"answer": "<text>"}')


@dataclass
class Recipe:
    """What one kind of step is allowed to see and do."""
    name: str
    budget: int                      # tokens for the context body
    tool_tags: tuple = ()            # which tools are offered
    sources: tuple = ()              # which sources may appear
    quotas: dict = field(default_factory=dict)
    allow_answer: bool = True        # False: must call a tool


class ContextEngine:
    def __init__(self, instructions, toolbox, chat, memory,
                 counter, recipes, subject, today, glossary=None):
        self.instructions = instructions
        self.toolbox = toolbox
        self.chat = chat
        self.memory = memory
        self.counter = counter
        self.recipes = {recipe.name: recipe for recipe in recipes}
        self.subject = subject
        self.today = today
        self.glossary = glossary or {}

    def item(self, source, content, priority=2, **meta):
        made = ContextItem(source, content, priority, meta)
        made.tokens = self.counter.count(content)
        return made

    def candidates(self, request_text, results) -> list[ContextItem]:
        """Everything that could go in, from every source."""
        day = f"Today is {self.today:%d %B %Y}."
        items = [self.item("today", day, priority=1)]
        query = expand(request_text, self.glossary)
        found = self.memory.recall(self.subject, query, self.today)
        for memory in found:
            items.append(self.item("memory", as_block([memory])))
        if self.chat.summary:
            items.append(self.item("summary", self.chat.summary))
        if self.chat.facts:
            items.append(self.item("state", self.chat.state_block()))
        window = self.chat.recent(120)
        if window:
            items.append(self.item("history", as_text(window)))
        items.append(self.item("request", request_text, priority=1))
        for n, (tool, text) in enumerate(results):
            items.append(self.item(
                "tool result", f"{tool} returned:\n{text}",
                priority=1, age=len(results) - n))
        return items

    def check(self, items, budget):
        """A hook for guards (Chapter 12): (items, flags)."""
        return items, []

    def show(self, item: ContextItem) -> str:
        """A hook for how one item is written into the context."""
        return render(item)

    def build(self, recipe_name, request_text, results=()) -> dict:
        """One request, shaped by the recipe for this step."""
        recipe = self.recipes[recipe_name]
        tools = self.toolbox.select(*recipe.tool_tags)
        system = self.instructions.render() + "\n\n" + (
            render_tools(tools, recipe.allow_answer) if tools
            else ANSWER_ONLY)
        allowed = [it for it in
                   self.candidates(request_text, results)
                   if it.priority == 1 or it.source in recipe.sources]
        allowed, flags = self.check(allowed, recipe.budget)
        query = expand(request_text, self.glossary)
        kept, dropped = select(allowed, query, recipe.budget,
                               recipe.quotas)
        kept = order_for_cache(kept)
        body = "\n\n".join(self.show(it) for it in kept)
        report = {"recipe": recipe.name,
                  "tools": [tool.name for tool in tools],
                  "system": self.counter.count(system),
                  "may_answer": recipe.allow_answer or not tools,
                  "body": {}, "flags": flags,
                  "dropped": [it.source for it in dropped]}
        for it in kept:
            report["body"][it.source] = (
                report["body"].get(it.source, 0) + it.tokens)
        return {"system": system, "report": report,
                "messages": [{"role": "user", "source": "context",
                              "content": body}]}


def run(engine, model, request_text, choose_recipe, max_steps=6):
    """The agent loop. Returns (answer, one report per step)."""
    results, reports = [], []
    for step in range(1, max_steps + 1):
        recipe = choose_recipe(step, results)
        request = engine.build(recipe, request_text, results)
        report = request["report"]
        reports.append(report)
        try:
            reply = parse_reply(model.complete(request))
        except ModelError as error:
            report["action"] = f"no usable reply ({error})"
            results.append(("engine", UNREADABLE))
            continue
        if "answer" in reply and report["may_answer"]:
            report["action"] = "answer"
            return reply["answer"], reports
        if "answer" in reply:
            report["action"] = "answered too early; sent back"
            results.append(("engine", TOO_EARLY))
            continue
        report["action"] = f"call {reply['tool']}"
        text = engine.toolbox.call(reply["tool"],
                                   reply.get("args", {}))
        results.append((reply["tool"], str(text)))
    return "Step limit reached. Passing to a human agent.", reports
