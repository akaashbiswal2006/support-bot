import time

from google import genai
from google.genai import types

from .config import TOP_K, MAX_DISTANCE, GEMINI_MODELS, get_api_key

FALLBACK = ("I could not find this in our support documents. "
            "Please contact our support team.")

SYSTEM_PROMPT = """You are a friendly customer support assistant for ShopEasy.
Rules:
1. Answer ONLY using the context given below. Never use outside knowledge.
2. If the context does not clearly contain the answer, reply exactly with: {fallback}
3. Keep answers short, clear and polite.
""".format(fallback=FALLBACK)


def retrieve(collection, question, k=TOP_K):
    """Find the k chunks that are most similar to the question."""
    result = collection.query(query_texts=[question], n_results=k)
    hits = []
    for text, meta, dist in zip(result["documents"][0],
                                result["metadatas"][0],
                                result["distances"][0]):
        hits.append({"text": text, "source": meta["source"], "distance": dist})
    return hits


def build_prompt(question, hits, history):
    context = "\n\n".join(f"[{h['source']}]\n{h['text']}" for h in hits)
    recent = "\n".join(f"{role}: {msg}" for role, msg in history[-4:])
    return (f"{SYSTEM_PROMPT}\nContext:\n{context}\n\n"
            f"Recent conversation:\n{recent}\n\n"
            f"Customer question: {question}\nAnswer:")


def call_gemini(api_key, prompt):
    """Try each model in turn. Returns (text, last_error)."""
    client = genai.Client(api_key=api_key,
                          http_options=types.HttpOptions(timeout=30000))
    last_error = None
    for model in GEMINI_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2),
                )
                text = (response.text or "").strip()
                if text:
                    return text, None
                last_error = RuntimeError("Empty response")
            except Exception as error:
                last_error = error
                print(f"Gemini error ({model}):", error)
                if type(error).__name__ == "ServerError" and attempt == 0:
                    time.sleep(1.5)
                    continue          # retry the same model once
                break                 # move on to the next model
    return None, last_error


def answer_question(collection, question, history=None):
    """Main backend function. Returns the answer, its sources and debug info."""
    history = history or []
    all_hits = retrieve(collection, question)
    hits = [h for h in all_hits if h["distance"] <= MAX_DISTANCE]

    if not hits:                         # nothing relevant in the documents
        return {"answer": FALLBACK, "sources": [], "debug": all_hits}

    api_key = get_api_key()
    if not api_key:
        msg = "API key missing. Add GEMINI_API_KEY to your .env file."
        return {"answer": msg, "sources": [], "debug": all_hits}

    answer, error = call_gemini(api_key, build_prompt(question, hits, history))
    if answer is None:
        if "429" in str(error):
            answer = "Too many requests right now. Please wait a minute and retry."
        else:
            answer = "Sorry, our assistant is busy right now. Please try again."
        return {"answer": answer, "sources": [], "debug": all_hits}

    if "could not find" in answer.lower():
        sources = []
    else:
        best = hits[0]["distance"]
        sources = sorted({h["source"] for h in hits
                          if h["distance"] <= best + 0.3})
    return {"answer": answer, "sources": sources, "debug": all_hits}