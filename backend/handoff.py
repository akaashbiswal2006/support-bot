import csv
import os
import re
from datetime import datetime, timedelta, timezone

from .config import BASE_DIR

CALLBACK_FILE = os.path.join(BASE_DIR, "data", "callback_requests.csv")

SUPPORT_PHONE = "1800-000-000"
OPEN_DAYS = range(0, 6)
OPEN_HOUR, CLOSE_HOUR = 9, 23
UTC_OFFSET_HOURS = 5.5

TOPICS = ["Returns and refunds", "Shipping and delivery",
          "Warranty claim", "Something else"]
TIME_SLOTS = ["As soon as possible", "Morning (9 AM - 12 PM)",
              "Afternoon (12 PM - 3 PM)", "Evening (3 PM - 6 PM)"]

PATTERNS = [
    r"\bcall\s*back\b",
    r"\bcall\s+me\b",
    r"\b(give|get)\s+me\s+a\s+call\b",
    r"\b(request|arrange|schedule|book)\s+(a\s+)?(phone\s+)?call\b",
    r"\b(talk|speak|connect|chat)\b.{0,30}\b(human|agent|executive|representative"
    r"|person|someone|support team|customer care|customer service)\b",
    r"\b(human|live|real)\s+(agent|support|person|being)\b",
    r"\bexecutive\b",
    r"\bphone\s+support\b",
    r"\bcall\s+support\b",
    r"\bcall\s+(an?\s+)?(agent|executive)\b",
]


def wants_human(text):
    """True when the customer asks for a call or a human executive."""
    t = text.lower()
    return any(re.search(p, t) for p in PATTERNS)


def local_now():
    return datetime.now(timezone.utc) + timedelta(hours=UTC_OFFSET_HOURS)


def is_open():
    t = local_now()
    return t.weekday() in OPEN_DAYS and OPEN_HOUR <= t.hour < CLOSE_HOUR


def handoff_message():
    if is_open():
        return ("I can arrange a call with one of our support executives. "
                "Please fill in the short form below and we will call you back "
                f"shortly. You can also call us directly on {SUPPORT_PHONE}.")
    return ("Our executives are available Monday to Saturday, 9 AM to 6 PM, and we "
            "are closed right now. Please leave your details below and we will call "
            f"you back when we open. You can also call us on {SUPPORT_PHONE} "
            "during support hours.")


def clean_phone(phone):
    return re.sub(r"[\s\-()]", "", phone or "")


def valid_phone(phone):
    return re.fullmatch(r"\+?\d{8,15}", clean_phone(phone)) is not None


def mask_phone(phone):
    p = clean_phone(phone)
    return "*" * max(len(p) - 4, 0) + p[-4:]


def _safe(value):
    """Stop spreadsheet formulas from running when the CSV is opened in Excel."""
    value = (value or "").strip()
    return "'" + value if value[:1] in ("=", "+", "-", "@") else value


def save_request(name, phone, topic, slot):
    """Append the request to data/callback_requests.csv and return a ticket id."""
    os.makedirs(os.path.dirname(CALLBACK_FILE), exist_ok=True)
    is_new = not os.path.exists(CALLBACK_FILE)
    now = local_now()
    ticket = "SE-" + now.strftime("%m%d-%H%M%S")
    with open(CALLBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["ticket", "created_at", "name", "phone",
                             "topic", "preferred_time"])
        writer.writerow([ticket, now.strftime("%Y-%m-%d %H:%M"), _safe(name),
                         clean_phone(phone), topic, slot])
    return ticket


def confirmation_message(name, phone, slot, ticket):
    return (f"Thank you, {name.strip()}. Your callback request **{ticket}** is "
            f"confirmed. An executive will call you on {mask_phone(phone)} "
            f"({slot.lower()}). If it is urgent you can also call "
            f"{SUPPORT_PHONE}.")