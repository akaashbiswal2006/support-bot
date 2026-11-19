from backend.ingest import build_index
from backend.rag import answer_question

collection = build_index()
result = answer_question(collection, "How many days do I have to return an item?")

print("ANSWER :", result["answer"])
print("SOURCES:", result["sources"])
for hit in result["debug"]:
    print("  distance", round(hit["distance"], 2), "|", hit["source"])