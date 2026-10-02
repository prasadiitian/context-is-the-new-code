"""ch04b_demo.py -- a fact changes, and the conversation doubles."""
from engine.conversation import Conversation
from engine.tokens import get_counter
from support_data import history

counter = get_counter()
chat = Conversation(counter)
for role, text in history():
    chat.add(role, text)
chat.note("fault logged", "yes, engineer to inspect the line")
chat.note("contact", "email only, no calls in work hours")


def sizes(label):
    window = chat.recent(budget=150)
    used = sum(turn.tokens for turn in window)
    state = counter.count(chat.state_block())
    print(f"{label:22}{len(chat.turns):4} turns"
          f"{chat.total_tokens():7} tokens in all"
          f"{used + state:6} sent")


sizes("after 38 turns")

# The customer changes their mind. The old value must not survive.
chat.add("user", "Actually my work email is down too. Call me, "
                 "but only after 6 in the evening.")
chat.add("assistant", "Understood. We will call after 6 pm.")
chat.note("contact", "phone, after 6 pm only")

# The conversation carries on for another 38 turns.
for role, text in history():
    chat.add(role, text)
sizes("after 78 turns")

print()
print("<state>")
print(chat.state_block())
print("</state>")
