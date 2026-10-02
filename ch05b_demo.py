"""ch05b_demo.py -- the cut-off, and an honest empty result."""
from engine.retrieval import in_force
from support_data import TODAY
from support_tools import INDEX, search_policies

QUESTIONS = [
    "My service was down for two days. Do I get a credit on my "
    "next bill?",
    "Do you sell mobile phone contracts?",
]

for question in QUESTIONS:
    print(f"query: {question}")
    hits = INDEX.search(question, k=5, where=in_force(TODAY))
    best = hits[0][0] if hits else 0
    for score, chunk in hits:
        verdict = "kept" if score >= 0.5 * best else "cut"
        print(f"  {score:5.2f}  {chunk.doc_id:15}{verdict}")
    print("  the tool returns:")
    for line in search_policies(question).splitlines():
        print(f"    {line}")
    print()
