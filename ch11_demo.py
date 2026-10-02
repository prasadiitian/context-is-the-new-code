"""ch11_demo.py -- a different context at every step."""
from engine.engine import run
from engine.model import get_model
from support_agent import build_engine, chooser
from support_data import REQUEST


def show(request_text, replies):
    engine = build_engine()
    model = get_model(replies)
    answer, reports = run(engine, model, request_text,
                          chooser(request_text))
    print(f"REQUEST: {request_text}")
    for step, report in enumerate(reports, start=1):
        body = sum(report["body"].values())
        tools = ", ".join(report["tools"]) or "none"
        print(f"step {step}: recipe '{report['recipe']}', "
              f"{report['action']}")
        print(f"  tools offered: {tools}")
        print(f"  system {report['system']} tokens, "
              f"context {body} tokens")
        for source, tokens in report["body"].items():
            print(f"    {source:12}{tokens:4}")
    print(f"answer ({model.name} model): {answer}")
    print()
    return model


model = show(REQUEST, [
    '{"tool": "lookup_account", "args": {"customer_id": "K-48213"}}',
    '{"tool": "search_policies", "args": {"query": "refund cancel"}}',
    '{"answer": "Our refund policy allows a full refund within 14 '
    'days of sign-up. Your account was opened 23 days ago, so it is '
    'outside that window and I cannot refund it. You can still '
    'cancel. I will send the details by email."}',
])

show("My connection keeps dropping. Is there an outage?", [
    '{"tool": "check_outage", "args": {"postal_code": "560001"}}',
    '{"answer": "There is no known outage in your area. A fault '
    'is already logged and an engineer will inspect the line. I '
    'will follow up by email."}',
])

if model.name == "scripted":
    print("--- context at the last step of the first request ---")
    print(model.requests[-1]["messages"][0]["content"])
