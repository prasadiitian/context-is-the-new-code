"""ch03_demo.py -- instructions as data, and a first model call."""
from engine.assembler import ContextAssembler
from engine.instructions import Instructions, lint
from engine.model import get_model
from engine.tokens import get_counter

counter = get_counter()

bad = Instructions()
bad.set("role", "You are a helpful assistant.")
bad.set("rules", "ALWAYS USE THE CURRENT POLICY. NEVER GIVE WRONG "
                 "ANSWERS. Be concise but thorough.")
print("lint, first draft:")
for warning in lint(bad):
    print("  -", warning)

good = Instructions()
good.set("role",
         "You are the support agent for a home broadband provider. "
         "You answer customers about billing, refunds and "
         "connection faults.")
good.set("rules", """\
- Answer only from the <policy> and <account> blocks below.
- If they do not cover the question, say you will pass it to a
  human agent.
- Use the date in the <today> block for any date arithmetic.
- State what the policy says, then whether this account meets it.""")
good.set("format",
         "Reply in under {max_words} words, in plain language.")
good.set("escalation",
         "If the customer asks for a manager or mentions a "
         "complaint, hand over to a human agent.")

print()
print("lint, second draft:", lint(good) or "no warnings")
system = good.render(max_words=80)
print(f"version {good.version()}, {counter.count(system)} tokens")
print()
print(system)

ctx = ContextAssembler(budget=300, counter=counter)
ctx.add("today", "Today is 10 March 2026.", priority=1)
ctx.add("policy", "Refunds: customers may cancel within 14 days "
                  "of sign-up for a full refund.", priority=1)
ctx.add("account", "Plan: Fibre 300. Signed up 15 February 2026, "
                   "23 days ago.", priority=1)
ctx.add("request", "Can I cancel and get my money back?", priority=1)

request = {"system": system, "messages": [
    {"role": "user", "source": "context", "content": ctx.build()}]}

model = get_model([
    "The policy allows a full refund within 14 days of sign-up. "
    "This account was opened 23 days ago, so it does not qualify. "
    "You can still cancel, and I can pass this to a human agent "
    "if you would like it reviewed."])
print()
print(f"model: {model.name}")
print(model.complete(request))
