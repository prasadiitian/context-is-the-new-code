"""ch06_demo.py -- what tools put into the context."""
import json

from engine.tools import (clip, from_mcp, mcp_text, parse_reply,
                          render_tools)
from engine.tokens import get_counter
from support_data import CUSTOMER, billing_record
from support_tools import build_toolbox

counter = get_counter()
box = build_toolbox()

everything = list(box.tools.values())
billing = box.select("billing")
print("1. tool definitions")
print(f"  all {len(everything)} tools: "
      f"{counter.count(render_tools(everything))} tokens")
print(f"  {len(billing)} billing tools: "
      f"{counter.count(render_tools(billing))} tokens")

raw = json.dumps(billing_record(CUSTOMER), indent=1)
shaped = box.call("lookup_account", {"customer_id": CUSTOMER})
print()
print("2. one tool result")
print(f"  raw record: {counter.count(raw)} tokens")
print(f"  shaped:     {counter.count(shaped)} tokens")
print(shaped)

print()
print("3. failures come back as text")
print(" ", box.call("check_outage", {"postal_code": "56 0001"}))
print(" ", box.call("refund_now", {}))

print()
print("4. an oversized result")
print(clip(raw, limit=20, counter=counter))

print()
print("5. parsing the model's reply")
call = '{"tool": "lookup_account", "args": {"customer_id": "K-1"}}'
print(" ", parse_reply(call))
print(" ", parse_reply("Sorry, I cannot help with that."))

# The shape an MCP server returns from tools/list and tools/call.
listing = {"tools": [{
    "name": "get_invoice",
    "description": "Fetch one invoice as text.",
    "inputSchema": {"type": "object", "properties": {
        "invoice_id": {"type": "string"}},
        "required": ["invoice_id"]}}]}


def fake_server(name, args):
    result = {"content": [{"type": "text",
                           "text": f"Invoice {args['invoice_id']}: "
                                   "paid in full."}],
              "isError": False}
    return mcp_text(result)


print()
print("6. a tool from an MCP listing")
for tool in from_mcp(listing, fake_server, tags=("billing",)):
    box.add(tool)
print(" ", box.call("get_invoice", {"invoice_id": "INV-7"}))
print(f"  billing tools now: {len(box.select('billing'))}")
