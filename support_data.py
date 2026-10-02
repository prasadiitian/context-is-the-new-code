"""support_data.py -- the support scenario used in every demo."""
from datetime import date

TODAY = date(2026, 3, 10)
CUSTOMER = "K-48213"
REQUEST = "Can I cancel and get my money back?"

OLD, NEW = date(2024, 1, 1), date(2026, 1, 1)


def doc(doc_id, title, text, effective=OLD, superseded=None):
    return {"id": doc_id, "title": title, "text": text,
            "effective": effective, "superseded": superseded}


POLICIES = [
    doc("refund-2024", "Refund policy",
        "Refunds: customers may cancel within 30 days of sign-up "
        "for a full refund. After 30 days the current month is "
        "not refunded.", superseded=NEW),
    doc("faq-2024", "Billing questions",
        "Can I cancel and get a refund? Yes. Customers may cancel "
        "within 30 days of sign-up for a full refund.",
        superseded=NEW),
    doc("terms-2024", "Terms of service, section 9",
        "Cancellation: customers may cancel within 30 days of "
        "sign-up for a full refund of fees paid.",
        superseded=NEW),
    doc("refund-2026", "Refund policy",
        "Refunds: customers may cancel within 14 days of sign-up "
        "for a full refund. After 14 days the current month is "
        "not refunded.", effective=NEW),
    doc("hardware", "Hardware returns",
        "Routers returned unopened within 30 days are refunded "
        "in full. Opened routers are refunded less a restocking "
        "fee."),
    doc("outage-credit", "Outage credits",
        "If a fault on our network lasts more than 24 hours, the "
        "customer receives a credit for each full day without "
        "service. Credits are applied to the next bill."),
    doc("plan-change", "Plan changes",
        "Customers may move to a faster plan at any time. Moving "
        "to a slower plan takes effect at the next billing date."),
]


def billing_record(customer_id: str) -> dict:
    """The raw 140-field row the billing system returns."""
    record = {"customer_id": customer_id, "plan": "Fibre 300"}
    record.update({f"field_{i:03}": None for i in range(3, 97)})
    record["signup_date"] = "2026-02-15"         # field 97 of 140
    record.update({f"field_{i:03}": None for i in range(98, 139)})
    record["postal_code"] = "560001"
    record["contact_channel"] = "phone"
    return record


USER_LINES = [
    "The light on the router is blinking orange again and the "
    "connection dropped a few minutes ago.",
    "I restarted it like you said and it came back for a while, "
    "then it dropped again.",
    "Now the light is solid white but the speed is very slow on "
    "every device in the house.",
    "It dropped again while I was on a work call. This keeps "
    "happening and I am losing patience.",
]
AGENT_LINES = [
    "Thanks for checking. Please unplug the router, wait thirty "
    "seconds, plug it back in and tell me which lights come on.",
    "I ran a line test from our side and it shows a weak signal. "
    "Please check the cable is pushed fully into the wall socket.",
    "I can see the connection is back. I will keep watching the "
    "line while you test it on one device.",
    "I am sorry this keeps happening. I have logged a fault so "
    "an engineer can look at the line.",
]
SPECIAL = {
    5: "I only signed up three weeks ago and it has dropped "
       "every few days since then.",
    9: "Please send any follow-up by email. I cannot take calls "
       "during work hours.",
}


def history() -> list[tuple[str, str]]:
    """38 turns: 19 from the customer, 19 from the agent."""
    turns = []
    for n in range(19):
        turns.append(("user", SPECIAL.get(n, USER_LINES[n % 4])))
        turns.append(("assistant", AGENT_LINES[n % 4]))
    return turns


# The domain's own words for what customers ask (Chapter 8).
GLOSSARY = {
    "cancel": "refund refunds signed sign up days",
    "money": "refund refunds",
}
