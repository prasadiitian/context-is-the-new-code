"""ch04_demo.py -- a window of recent turns plus settled facts."""
from engine.conversation import Conversation, as_text
from engine.tokens import get_counter
from support_data import history

counter = get_counter()
chat = Conversation(counter)
for role, text in history():
    chat.add(role, text)

print(f"{len(chat.turns)} turns, {chat.total_tokens()} tokens")

# Facts the application learned along the way.
chat.note("router light", "blinking orange, then solid white")
chat.note("restarts tried", "3")
chat.note("line test", "weak signal")
chat.note("fault logged", "yes, engineer to inspect the line")
chat.note("customer said", "signed up three weeks ago")
chat.note("contact", "email only, no calls in work hours")

window = chat.recent(budget=150)
state = chat.state_block()
print(f"window: {len(window)} turns, "
      f"{sum(t.tokens for t in window)} tokens")
print(f"state:  {len(chat.facts)} facts, "
      f"{counter.count(state)} tokens")
print()
print("<state>")
print(state)
print("</state>")
print()
print("<history>")
print(as_text(window))
print("</history>")
