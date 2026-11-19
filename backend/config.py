import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")

COLLECTION_NAME = "support_docs"
CHUNK_SIZE = 130
CHUNK_OVERLAP = 80
TOP_K = 4
MAX_DISTANCE = 1.35

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
GEMINI_MODELS = [m.strip() for m in os.getenv(
    "GEMINI_MODELS", "gemini-3.1-flash-lite,gemini-3.5-flash").split(",")]


def get_api_key():
    """Look in .env / environment first, then in Streamlit secrets (deployment)."""
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return None