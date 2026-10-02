"""ch06b_demo.py -- shaping a result that is a list."""
import json

from engine.tokens import get_counter

counter = get_counter()


def invoice_rows(customer_id: str) -> list[dict]:
    """What the billing system returns: two years of invoices."""
    rows = []
    for n in range(24):
        rows.append({
            "invoice_id": f"INV-{1000 + n}",
            "customer_id": customer_id,
            "period": f"{2024 + n // 12}-{n % 12 + 1:02}",
            "amount": 899.0, "currency": "INR",
            "status": "paid" if n < 23 else "due",
            "tax_code": "T1", "ledger_ref": None, "batch": n * 7})
    return rows


def recent_invoices(customer_id: str, keep: int = 3) -> str:
    """The newest invoices, a count of the rest, and the total due."""
    rows = invoice_rows(customer_id)
    due = [row for row in rows if row["status"] != "paid"]
    owed = sum(row["amount"] for row in due)
    lines = [f"{row['period']}: {row['amount']:.2f} "
             f"{row['currency']}, {row['status']}"
             for row in rows[-keep:]]
    lines.append(f"Showing the newest {keep} of {len(rows)} "
                 "invoices.")
    lines.append(f"Unpaid invoices: {len(due)}, total {owed:.2f} "
                 f"{rows[0]['currency']}.")
    return "\n".join(lines)


raw = json.dumps(invoice_rows("K-48213"), indent=1)
shaped = recent_invoices("K-48213")
print(f"raw list: {counter.count(raw)} tokens")
print(f"shaped:   {counter.count(shaped)} tokens")
print(shaped)
