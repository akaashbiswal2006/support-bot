import time

from backend.ingest import build_index
from backend.rag import answer_question


TESTS = [
    ("How many days do I have to return an item?", "30"),
    ("How long does a refund take?", "7"),
    ("How long does standard shipping take?", "3-5"),
    ("Is shipping free?", "50"),
    ("How long is the warranty on electronics?", "12"),
    ("What are your support hours?", "9"),
    ("Does the warranty cover accidental damage?", "manufacturing"),
    ("Can I return a sale item?", "exchange"),
    ("How do I start a return?", "my orders"),
    ("How much does express shipping cost?", "12.99"),
    ("How long does express shipping take?", "2 days"),
    ("What is the cost of standard shipping?", "4.99"),
    ("Do you ship internationally?", "country"),
    ("Will I get a tracking number?", "tracking"),
    ("What do I need to make a warranty claim?", "order number"),
    ("What is your support email?", "help@shopeasy"),
    ("What is your phone number?", "1800"),
    ("What is the CEO's favourite colour?", "could not find"),
    ("Do you sell laptops?", "could not find"),
    ("Who won the cricket world cup?", "could not find"),
]

collection = build_index()
correct = 0

for question, keyword in TESTS:
    result = answer_question(collection, question)
    ok = keyword.lower() in result["answer"].lower()
    correct += ok
    print("PASS" if ok else "FAIL", "|", question)
    if not ok:
        print("      got:", result["answer"])
    time.sleep(4)

print(f"\nAccuracy: {correct}/{len(TESTS)} = {100 * correct / len(TESTS):.0f}%")